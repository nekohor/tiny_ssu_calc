# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib
from dateutil.parser import parse
from datetime import datetime
import seaborn as sns
# matplotlib.use('Agg')
import matplotlib.pyplot as plt

from lpce import LateralPiece
from lrg import LateralRollGap
from ufd import UniForcDist
from crlc import CompositeRollStackCrown

from targt import Target

from utils import mathuty
import logging
logging.basicConfig(level=logging.INFO, filename="print.log")

sns.set(color_codes=True)
sns.set(rc={'font.family': [u'Microsoft YaHei']})
sns.set(rc={'font.sans-serif': [u'Microsoft YaHei', u'Arial',
                                u'Liberation Sans', u'Bitstream Vera Sans',
                                u'sans-serif']})


class Allocation():

    def __init__(self, fsstd, lpce, lrg, ufd, crlc, penv):
        self.fsstd = fsstd

        self.lpce = lpce
        self.lrg = lrg
        self.ufd = ufd
        self.crlc = crlc

        self.penv = penv
        self.targt = Target(self.fsstd, self.lpce, self.lrg,
                            self.ufd, self.crlc, self.penv, self)

        self.d = pd.DataFrame()
        self.std_vec = [1, 2, 3, 4, 5, 6, 7]

        self.loop_count = 0
        self.loop_count_lim = 10
        self.start_over = False
        self.redrft_perm = False

    def Calculate(self):
        PceIZFSPass = 0
        CritFSPass = 7

        self.d.loc[0, "thick"] = self.fsstd.d.loc[1, "en_thick"]

        for std in self.std_vec:
            self.d.loc[std, "force_pu_wid"] = (
                self.fsstd.d.loc[std, "force_strip"] /
                self.fsstd.d.loc[std, "en_width"])

            self.d.loc[std, "thick"] = self.fsstd.d.loc[std, "ex_thick"]

            # *pcFSPassD->pcAlcD->pcRollbite =
            #     *pcFSPassD->pcFSStdD[ iter ]->pcRollbite;

            if self.lrg.d.loc[std, "pce_infl_cof"] <= 0:
                PceIZFSPass = std

        # if redrft_perm: Frc_Chg_Limits

        pu_prf_change_sum = 0
        for std in self.std_vec[:-1]:

            if ((self.fsstd.d.loc[std, "dummied"] != "T") &
                    (self.lrg.d.loc[std, "pce_infl_cof"] > 0)):
                pass
            else:
                raise Exception("pce_infl_cof <= 0")

            if self.lpce.d.loc[std, "strn_rlf_cof"] == 0:
                pu_prf_change_sum += (1 / self.lrg.d.loc[std, "pce_infl_cof"])
            else:
                pu_prf_change_sum += (
                    self.lpce.d.loc[std, "strn_rlf_cof"] /
                    (self.lrg.d.loc[std, "pce_infl_cof"] *
                     self.lpce.d.loc[std, "elas_modu"]))
            print("pu_prf_change_sum", std)
            print(pu_prf_change_sum)

        self.targt = Target(self.fsstd, self.lpce, self.lrg,
                            self.ufd, self.crlc, self.penv, self)
        ef_en_pu_prf, ef_ex_pu_prf, istd_ex_strn = self.targt.Delvry_Pass()

        std = 7
        while std != 0:
            # 在alcd对象中这里的stdd局部对象实际就为当前机架道次的fsstd对象
            pce_wr_crn, wr_br_crn = self.crlc.Crns(
                std, self.fsstd.d.loc[std, "wr_shft"])
            print("pce_wr_crn by crlc crns before actrtyp_shft", std)
            print(pce_wr_crn)
            # print(" wr_br_crn by crlc crns before actrtyp_shft", std)
            # print(wr_br_crn)

            if self.fsstd.d.loc[std, "dummied"] == "T":
                self.d.loc[std - 1, "thick"] = self.d.loc[std, "thick"]
                self.d.loc[std, "ufd_pu_prf"] = 0
            else:
                # 925-1775 line else
                # self.rollbite.Calculate()

                # if redrft_perm: cAlcD::Eval_Frc_PU_Wid
                flt_ok = True

                if std < PceIZFSPass:
                    self.d.loc[std, "ufd_pu_prf"] = self.ufd.Prf(
                        self.d.loc[std, "force_pu_wid"],
                        self.fsstd.d.loc[std, "force_bnd"],
                        pce_wr_crn,
                        wr_br_crn) / self.d.loc[std, "thick"]
                else:
                    self.d.loc[std, "ufd_pu_prf"] = self.lrg.calc(
                        std, "UFD_PU_Prf3")(ef_en_pu_prf, ef_ex_pu_prf)
                    print("pass{}".format(std))
                    print("ef_en_pu_prf: {}".format(ef_en_pu_prf))
                    print("ef_ex_pu_prf: {}".format(ef_ex_pu_prf))

                    pce_wr_crn, wr_br_crn = self.actrtyp_shift(
                        std, pce_wr_crn, wr_br_crn)

                    print("pce_wr_crn after actrtyp_shft", std)
                    print(pce_wr_crn)
                    # print(" wr_br_crn after actrtyp_shft", std)
                    # print(wr_br_crn)

                    self.actrtyp_bend(std, pce_wr_crn, wr_br_crn)

                    self.lpce.d.loc[std, "ufd_pu_prf"] = self.ufd.Prf(
                        std,
                        self.d["force_pu_wid"][std],
                        self.fsstd.d["force_bnd"][std],
                        pce_wr_crn, wr_br_crn) / self.d.loc[std, "thick"]
                    # end if down stream stand influence is 0

                ufd_pu_prf_tol = 0.0001
                alc_lim = (
                    abs(self.d.loc[std, "ufd_pu_prf"] -
                        self.lpce.d.loc[std, "ufd_pu_prf"]) > ufd_pu_prf_tol)

                print("  alc ufd_pu_prf {}".format(std))
                print(self.d.loc[std, "ufd_pu_prf"])
                print(" lpce ufd_pu_prf {}".format(std))
                print(self.lpce.d.loc[std, "ufd_pu_prf"])
                print("alc_lim", alc_lim)

                redrft_lim = False
                # redrft_lim = false; if( redrft_perm  )  1183-1475line

                if alc_lim | redrft_lim:
                    # 1481-1734 alc_lim check
                    ufd_pu_prf = self.ufd.Prf(
                        std,
                        self.d["force_pu_wid"][std],
                        self.fsstd.d["force_bnd"][std],
                        pce_wr_crn, wr_br_crn) / self.d["thick"][std]
                    print("local ufd_pu_prf", std)
                    print(self.lpce.d.loc[std, "ufd_pu_prf"])

                    ef_en_pu_prf_buf = self.lrg.calc(
                        std, "Ef_En_PU_Prf3")(
                        ufd_pu_prf, ef_en_pu_prf, ef_ex_pu_prf)

                    if ((ef_en_pu_prf_buf >
                         self.penv.d["ef_pu_prf_env_max"][std - 1]) |
                        (ef_en_pu_prf_buf <
                         self.penv.d["ef_pu_prf_env_min"][std - 1])):
                        if ef_en_pu_prf < ef_ex_pu_prf:
                            if ef_en_pu_prf_buf > ef_ex_pu_prf:
                                ef_en_pu_prf_buf = ef_ex_pu_prf
                        else:
                            if ef_en_pu_prf_buf < ef_ex_pu_prf:
                                ef_en_pu_prf_buf = ef_ex_pu_prf
                    ef_en_pu_prf = ef_en_pu_prf_buf

                    std_ex_strn = self.lrg.calc(
                        std, "Std_Ex_Strn1")(ef_en_pu_prf, ufd_pu_prf)

                    ef_ex_pu_prf = self.lrg.calc(
                        std, "Ef_Ex_PU_Prf3")(ef_en_pu_prf, ufd_pu_prf)

                    if std < 7:
                        # Calculate the stand exit differential strain
                        # relative to the next non-dummied pass.
                        std_ex_strn_dn = self.lrg.calc(
                            std + 1, "Std_Ex_Strn4")(
                            ef_ex_pu_prf,
                            self.lpce.d.loc[std + 1, "ef_pu_prf"])

                        flt_idx_list = ["we", "cb"]
                        bckl_lim_dn = {}
                        for flt_idx in flt_idx_list:
                            bckl_lim_dn[flt_idx] = (
                                self.lpce.d.loc[
                                    std + 1,
                                    "crit_bckl_lim_{}".format(flt_idx)])

                    if std == 7:
                        flt_ok = (
                            (std_ex_strn <=
                                self.lpce.d.loc[std, "crit_bckl_lim_we"]) &
                            (std_ex_strn >=
                                self.lpce.d.loc[std, "crit_bckl_lim_cb"]))
                    else:
                        flt_ok = (
                            (std_ex_strn <=
                                self.lpce.d.loc[std, "crit_bckl_lim_we"]) &
                            (std_ex_strn >=
                                self.lpce.d.loc[std, "crit_bckl_lim_cb"]) &
                            (std_ex_strn_dn <= bckl_lim_dn["we"]) &
                            (std_ex_strn_dn >= bckl_lim_dn["cb"]))

                    if not flt_ok:
                        if std != 7:
                            flt_ok = (
                                (std_ex_strn_dn <= bckl_lim_dn["we"]) &
                                (std_ex_strn_dn >= bckl_lim_dn["cb"]))

                        # Re-target the per unit profile
                        if ((not flt_ok) &
                            (self.loop_count <= self.loop_count_lim) &
                                (std <= CritFSPass)):
                            ef_pu_prf_alt = self.targt.Pass_Mill_Targ(std)
                            std_ex_strn = self.lrg.calc(
                                std, "Std_Ex_Strn2")(istd_ex_strn)

                            pu_prf = self.lrg.calc(
                                std, "Istd_Ex_PU_Prf0")(
                                std_ex_strn, ef_pu_prf_alt)
                            pu_prf = mathuty.Clamp(
                                pu_prf,
                                self.penv.d.loc[7, "pu_prf_env_min"],
                                self.penv.d.loc[7, "pu_prf_env_max"])

                            pu_prf_same = self.targt.Limit_PU_Prf(pu_prf)

                            CritFSPass = std

                            if not pu_prf_same:
                                self.start_over = True
                    # end of alc_lim check

                self.lpce.d.loc[std, "ufd_pu_prf"] = self.ufd.Prf(
                    std,
                    self.d["force_pu_wid"][std],
                    self.fsstd.d["force_bnd"][std],
                    pce_wr_crn, wr_br_crn) / self.d["thick"][std]

                self.lpce.d.loc[std, "ef_pu_prf"] = self.lrg.calc(
                    std, "Ef_Ex_PU_Prf3")(
                    ef_en_pu_prf, self.lpce.d.loc[std, "ufd_pu_prf"])

                self.lpce.d.loc[std, "strn"] = self.lrg.calc(
                    std, "Std_Ex_Strn4")(
                    ef_en_pu_prf, self.lpce.d.loc[std, "ef_pu_prf"])

                self.lpce.d.loc[std, "prf"] = self.lrg.calc(
                    std, "Istd_Ex_PU_Prf0")(
                    self.lpce.d.loc[std, "strn"],
                    self.lpce.d.loc[std, "ef_pu_prf"]) * self.d["thick"][std]

                # end of pass not dummied

            if self.start_over:
                self.loop_count = self.loop_count + 1

                if self.loop_count > self.loop_count_lim:
                    raise Exception(
                        "Calculate: loop counter exceeded configured limit")

                self.start_over = False
                std = 7  # pcFSPassD = pcLstFSPassD;

                # if ( redrft_perm ): cAlcD::Frc_Chg_Limits

                tmp = self.targt.Delvry_Pass()
                ef_en_pu_prf = tmp[0]
                ef_ex_pu_prf = tmp[1]
                istd_ex_strn = tmp[2]

                self.lpce.d.loc[7, "ef_pu_prf"] = ef_ex_pu_prf
            else:
                if std == 1:
                    break
                else:
                    std = std - 1
                ef_ex_pu_prf = ef_en_pu_prf

                ef_en_pu_prf = mathuty.Clamp(
                    ef_ex_pu_prf,
                    self.penv.d["ef_pu_prf_env_min"][PceIZFSPass],
                    self.penv.d["ef_pu_prf_env_max"][PceIZFSPass])

                ef_pu_prf_sum = 0
                buf_pass = PceIZFSPass + 1
                while (buf_pass <= 7) & (buf_pass > 0):
                    self.d.loc[buf_pass, "ef_pu_prf_dlt_min"] = max(
                        self.lrg.d.loc[buf_pass, "ef_pu_prf_chg_cb"],
                        max(ef_ex_pu_prf,
                            self.penv.d.loc[buf_pass, "ef_pu_prf_env_min"]) -
                        min(ef_en_pu_prf,
                            self.penv.d.loc[buf_pass - 1,
                                            "ef_pu_prf_env_max"]))

                    self.d.loc[buf_pass, "ef_pu_prf_dlt_max"] = min(
                        self.lrg.d.loc[buf_pass, "ef_pu_prf_chg_we"],
                        min(ef_ex_pu_prf,
                            self.penv.d.loc[buf_pass, "ef_pu_prf_env_max"]) -
                        max(ef_en_pu_prf,
                            self.penv.d.loc[buf_pass - 1,
                                            "ef_pu_prf_env_min"]))

                    if ef_en_pu_prf <= ef_ex_pu_prf:
                        ef_pu_prf_sum = (
                            ef_pu_prf_sum +
                            self.d.loc[buf_pass, "ef_pu_prf_dlt_max"])

                        if buf_pass == std:
                            if ef_pu_prf_sum <= 0.000001:
                                ef_en_pu_prf = ef_ex_pu_prf
                            else:
                                ef_en_pu_prf = (
                                    ef_ex_pu_prf -
                                    self.d.loc[buf_pass, "ef_pu_prf_dlt_max"] *
                                    (ef_ex_pu_prf - ef_en_pu_prf) /
                                    ef_pu_prf_sum)
                        else:
                            if (self.penv.d.loc[
                                    buf_pass,
                                    "ef_pu_prf_env_max"] <= ef_en_pu_prf):
                                ef_en_pu_prf = self.penv.d.loc[
                                    buf_pass,
                                    "ef_pu_prf_env_max"]
                                ef_pu_prf_sum = 0
                            if (self.penv.d.loc[
                                buf_pass, "ef_pu_prf_env_min"] >=
                                    ef_ex_pu_prf):
                                ef_en_pu_prf = self.penv.d.loc[
                                    buf_pass,
                                    "ef_pu_prf_env_min"]
                                ef_pu_prf_sum = 0
                    else:
                        ef_pu_prf_sum = (
                            ef_pu_prf_sum +
                            self.d.loc[buf_pass, "ef_pu_prf_dlt_min"])

                        if buf_pass == std:
                            if ef_pu_prf_sum >= -0.000001:
                                ef_en_pu_prf = ef_ex_pu_prf
                            else:
                                ef_en_pu_prf = (
                                    ef_ex_pu_prf -
                                    self.d.loc[buf_pass, "ef_pu_prf_dlt_min"] *
                                    (ef_ex_pu_prf - ef_en_pu_prf) /
                                    ef_pu_prf_sum)
                        else:
                            if (self.penv.d.loc[
                                    buf_pass,
                                    "ef_pu_prf_env_min"] >= ef_en_pu_prf):
                                ef_en_pu_prf = self.penv.d.loc[
                                    buf_pass,
                                    "ef_pu_prf_env_min"]
                                ef_pu_prf_sum = 0
                            if (self.penv.d.loc[
                                    buf_pass,
                                    "ef_pu_prf_env_max"] <= ef_ex_pu_prf):
                                ef_en_pu_prf = self.penv.d.loc[
                                    buf_pass,
                                    "ef_pu_prf_env_max"]
                                ef_pu_prf_sum = 0

                    if buf_pass == std:
                        break
                    else:
                        buf_pass = buf_pass + 1

                # Calculate initial entry pu profile
                if self.lpce.d["strn_rlf_cof"][std] == 0:
                    self.d.loc[std, "pu_prf_change"] = (
                        1 / self.lrg.d.loc[std, "pce_infl_cof"] /
                        pu_prf_change_sum)
                else:
                    self.d.loc[std, "pu_prf_change"] = (
                        self.lpce.d["strn_rlf_cof"][std] /
                        (self.lrg.d.loc[std, "pce_infl_cof"] *
                         self.lpce.d["elas_modu"][std]) / pu_prf_change_sum)

                ef_en_pu_prf_dft = (
                    ef_ex_pu_prf +
                    (self.targt.en_pu_prf - self.targt.pu_prf) *
                    self.d.loc[std, "pu_prf_change"])

                if (((ef_en_pu_prf_dft > ef_ex_pu_prf) & (
                    ef_en_pu_prf_dft < ef_en_pu_prf)) | ((
                        ef_en_pu_prf_dft < ef_ex_pu_prf) & (
                        ef_en_pu_prf_dft > ef_en_pu_prf))):
                    ef_en_pu_prf = ef_en_pu_prf_dft

                ef_en_pu_prf = self.targt.Eval_Ef_En_PU_Prf(
                    ef_ex_pu_prf,
                    self.lrg.d["ef_pu_prf_chg_cb"][std],
                    self.lrg.d["ef_pu_prf_chg_we"][std],
                    self.penv.d["ef_pu_prf_env_min"][std - 1],
                    self.penv.d["ef_pu_prf_env_max"][std - 1],
                    ef_en_pu_prf)

            # end of start_over not true
        # end of while loop
        print("PceIZFSPass", PceIZFSPass)
        self.redrfted = False
        if self.redrft_perm:
            pass
        else:
            for std in self.std_vec:
                self.fsstd.d.loc[std, "force_ssu"] = 0

    def actrtyp_shift(self, std, pce_wr_crn_org, wr_br_crn_org):
        if self.crlc.cfg_prof.loc[std, "rprof"] != "parab":
            pce_wr_crn_buf, wr_br_crn_buf = self.ufd.Crns(
                std,
                self.d["ufd_pu_prf"][std] * self.d["thick"][std],
                self.d["force_pu_wid"][std],
                self.fsstd.d["force_bnd"][std],
                pce_wr_crn_org, wr_br_crn_org)

            print("pce_wr_crn by ufd.crns in actrtyp_shft", std)
            print(pce_wr_crn_buf)
            # print(" wr_br_crn by ufd.crns in actrtyp_shft", std)
            # print(wr_br_crn_buf)

            self.fsstd.d.loc[std, "wr_shft"] = self.crlc.Shft_Pos(
                std,
                pce_wr_crn_buf,
                self.fsstd.lim["wr_shft_lim_min"][std],
                self.fsstd.lim["wr_shft_lim_max"][std],
                self.fsstd.d["wr_shft"][std])

            self.deal_with_lock_pos_shft(std)

            pce_wr_crn_buf, wr_br_crn_buf = self.crlc.Crns(
                std, self.fsstd.d["wr_shft"][std])
            return pce_wr_crn_buf, wr_br_crn_buf
        else:
            return pce_wr_crn_org, wr_br_crn_org

    def actrtyp_bend(self, std, pce_wr_crn, wr_br_crn):
        tmp = self.ufd.Bnd_Frc(
            std,
            self.d["ufd_pu_prf"][std] * self.d["thick"][std],
            self.d["force_pu_wid"][std],
            pce_wr_crn,
            wr_br_crn,
            self.fsstd.lim["force_bnd_lim_min"][std],
            self.fsstd.lim["force_bnd_lim_max"][std])

        self.fsstd.d.loc[std, "force_bnd"] = tmp[0]
        self.fsstd.d.loc[std, "force_bnd_des"] = tmp[1]
        print("force_bnd     after actrtyp_bend", std)
        print(self.fsstd.d.loc[std, "force_bnd"])
        print("force_bnd_des after actrtyp_bend", std)
        print(self.fsstd.d.loc[std, "force_bnd_des"])

    def deal_with_lock_pos_shft(self, std):
        if np.isnan(self.fsstd.d["wr_shft_lock"][std]):
            pass
        else:
            # self.fsstd.d.loc[std, "wr_shft"] = (mathuty.Clamp(
            #     self.fsstd.d["wr_shft_lock"][std],
            #     self.fsstd.lim["wr_shft_lim_min"][std],
            #     self.fsstd.lim["wr_shft_lim_max"][std]))

            self.fsstd.d.loc[std, "wr_shft"] = (
                self.fsstd.d["wr_shft_lock"][std])
