# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib
from dateutil.parser import parse
from datetime import datetime
import seaborn as sns
import os
import sys
import docx
from docx.shared import Inches
import openpyxl
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.append("e:/box/")

import logging
logging.basicConfig(level=logging.INFO, filename="print.log")

sns.set(color_codes=True)
sns.set(rc={'font.family': [u'Microsoft YaHei']})
sns.set(rc={'font.sans-serif': [u'Microsoft YaHei', u'Arial',
                                u'Liberation Sans', u'Bitstream Vera Sans',
                                u'sans-serif']})


class Allocation():

    def __init__(self, fsstd, evllpce, targt, crlc, ufd):
        self.fsstd = fsstd
        self.evllpce = evllpce
        self.targt = targt
        self.crlc = crlc
        self.ufd = ufd
        self.d = pd.DataFrame()
        self.std_vec = [1, 2, 3, 4, 5, 6, 7]

        self.loop_count = 0
        self.loop_count_lim = 10
        self.start_over = False
        self.redrft_perm = False

    def Calculate(self):
        self.d.loc[0, "thick"] = self.fsstd.d.loc[1, "en_thick"]

        PceIZFSPass = 0
        for std in self.std_vec:
            self.d.loc[std, "force_pu_wid"] = (
                self.fsstd.d.loc[std, "force_strip"] /
                self.fsstd.d.loc[std, "en_width"])

            self.d.loc[std, "thick"] = self.fsstd.d.loc[std, "ex_thick"]

            # *pcFSPassD->pcAlcD->pcRollbite =
            #     *pcFSPassD->pcFSStdD[ iter ]->pcRollbite;

            if self.fsstd.lrg.d.loc[std, "pce_infl_cof"] <= 0:
                PceIZFSPass += 1

        # if redrft_perm: Frc_Chg_Limits

        pu_prf_change_sum = 0
        for std in self.std_vec:
            if self.evllpce.d.loc[std, "strn_rlf_cof"] == 0:
                pu_prf_change_sum += self.fsstd.lrg.d.loc[std, "pce_infl_cof"]
            else:
                pu_prf_change_sum += (
                    self.evllpce.d.loc[std, "strn_rlf_cof"] /
                    self.fsstd.lrg.d.loc[std, "pce_infl_cof"] *
                    self.evllpce.d.loc[std, "elas_modu"])

        ef_en_pu_prf, ef_ex_pu_prf, istd_ex_strn = self.targt.Delvry_Pass()

        std = 7
        while std != 0:
            # 在alcd对象中这里的stdd局部对象实际就为当前机架道次的fsstd对象
            pce_wr_crn, wr_br_crn = crlc.Crns(
                std, self.fsstd.d[std, "wr_shft"])

            if self.fsstd.d.loc[std, "dummied"] == "T":
                self.d.loc[std - 1, "thick"] = self.d.loc[std, "thick"]
                self.d.loc[std, "ufd_pu_prf"] = 0
            else:
                # 925-1775 line else
                self.rollbite.Calculate()

                # if redrft_perm: cAlcD::Eval_Frc_PU_Wid

                flt_ok = True

                if std < PceIZFSPass:
                    self.d.loc[std, "ufd_pu_prf"] = self.ufd.Prf(
                        self.d.loc[std, "force_pu_wid"],
                        self.fsstd.d.loc[std, "force_bnd"],
                        pce_wr_crn,
                        wr_br_crn)
                else:
                    self.d.loc[std, "ufd_pu_prf"] = self.fsstd.lrg.calc(
                        std, "UFD_PU_Prf3")(ef_en_pu_prf, ef_ex_pu_prf)
                    pce_wr_crn, wr_br_crn = self.actrtyp_shift(
                        std, pce_wr_crn, wr_br_crn)
                    self.actrtyp_bend(std, pce_wr_crn, wr_br_crn)

                    self.lpce.d.loc[std, "ufd_pu_prf"] = self.ufd.Prf(
                        std,
                        self.d["force_pu_wid"][std],
                        self.fsstd.d["force_bnd"][std],
                        pce_wr_crn, wr_br_crn)
                    # end if down stream stand influence is 0
                ufd_pu_prf_tol = 0.0001
                alc_lim = (
                    abs(self.d.loc[std, "ufd_pu_prf"] -
                        self.lpce.d.loc[std, "ufd_pu_prf"]) > ufd_pu_prf_tol)

                redrft_lim = False
                # redrft_lim = false; if( redrft_perm  )  1183-1475line

                if alc_lim | redrft_lim:
                    # 1481-1734 alc_lim check
                    ufd_pu_prf = self.ufd.Prf(
                        std,
                        self.d["force_pu_wid"][std],
                        self.fsstd.d["force_bnd"][std],
                        pce_wr_crn, wr_br_crn)

                    ef_en_pu_prf_buf = self.fsstd.lrg.calc(
                        std, "Ef_En_PU_Prf3")(
                        ufd_pu_prf, ef_en_pu_prf, ef_ex_pu_prf)

                    if (ef_en_pu_prf_buf > self.penv.d[std - 1, "ef_pu_prf_env_max"]) |
                        (ef_en_pu_prf_buf < self.penv.d[std - 1, "ef_pu_prf_env_min"]):
                        if ef_en_pu_prf < ef_ex_pu_prf:
                            if ef_en_pu_prf_buf > ef_ex_pu_prf:
                                ef_en_pu_prf_buf = ef_ex_pu_prf
                        else:
                            if ef_en_pu_prf_buf < ef_ex_pu_prf:
                                ef_en_pu_prf_buf = ef_ex_pu_prf

                    ef_en_pu_prf = ef_en_pu_prf_buf

                    std_ex_strn = self.fsstd.lrg.calc(
                        std, "Std_Ex_Strn1")(ef_en_pu_prf, ufd_pu_prf)

                    ef_ex_pu_prf = self.fsstd.lrg.calc(
                        std, "Ef_Ex_PU_Prf3")(ef_en_pu_prf, ufd_pu_prf)

                    if std < 7:
                        # Calculate the stand exit differential strain relative to
                        # the next non-dummied pass.
                        std_ex_strn_dn = self.fsstd.lrg.calc(
                            std + 1, "Std_Ex_Strn4")(ef_ex_pu_prf, self.lpce.d[std + 1, "ef_pu_prf"])

                        flt_idx_list = ["we", "cb"]
                        bckl_lim_dn = {}
                        for flt_idx in flt_idx_list:
                            bckl_lim_dn[flt_idx] = self.lpce.d[std +
                                                               1, "crit_bckl_lim_{}".format(flt_idx)]

                    if std == 7:
                        flt_ok = (
                            (std_ex_strn <= self.lpce.d[std, "crit_bckl_lim_we"]) &
                            (std_ex_strn >= self.lpce.d[std, "crit_bckl_lim_cb"]))
                    else:
                        flt_ok = (
                            (std_ex_strn <= self.lpce.d[std, "crit_bckl_lim_we"]) &
                            (std_ex_strn >= self.lpce.d[std, "crit_bckl_lim_cb"]) &
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
                                (std <= 7)):
                            ef_pu_prf_alt = self.targt.Pass_Mill_Targ()
                            std_ex_strn = self.fsstd.lrg.calc(
                                std, "Std_Ex_Strn2")(istd_ex_strn)
                            pu_prf = self.fsstd.lrg.calc(
                                std, "Istd_Ex_PU_Prf0")(std_ex_strn, ef_pu_prf_alt)
                            pu_prf = mathuty.Clamp(
                                pu_prf,
                                self.penv.d[7, "pu_prf_env_min"],
                                self.penv.d[7, "pu_prf_env_max"])

                            pu_prf_same = self.targt.Limit_PU_Prf(pu_prf)

                            # pcCritFSPassD = pcFSPassD;

                            if not pu_prf_same:
                                self.start_over = True
                    # end of alc_lim check

                self.lpce.d.loc[std, "ufd_pu_prf"] = self.ufd.Prf(
                    std,
                    self.d["force_pu_wid"][std],
                    self.fsstd.d["force_bnd"][std],
                    pce_wr_crn, wr_br_crn)

                self.lpce.d.loc[std, "ef_pu_prf"] = self.fsstd.lrg.calc(
                    std, "Ef_Ex_PU_Prf3")(ef_en_pu_prf, self.lpce.d.loc[std, "ufd_pu_prf"])

                self.lpce.d.loc[std, "strn"] = self.fsstd.lrg.calc(
                    std, "Std_Ex_Strn4")(ef_en_pu_prf, self.lpce.d.loc[std, "ef_pu_prf"])

            if self.start_over:
                self.loop_count = self.loop_count + 1

                if self.loop_count > loop_count_lim:
                    raise Exception(
                        "Calculate: loop counter exceeded configured limit")

                start_over = False
                std = 7  # pcFSPassD = pcLstFSPassD;

                # if ( redrft_perm ): cAlcD::Frc_Chg_Limits

                ef_en_pu_prf, ef_ex_pu_prf, istd_ex_strn = self.targt.Delvry_Pass()

                self.lpce.d.loc[7, "ef_pu_prf"] = ef_ex_pu_prf
            else:
                if std == 1:
                    break
                else:
                    std = std - 1
                ef_ex_pu_prf = ef_en_pu_prf

                ef_en_pu_prf = mathuty.Clamp(
                    ef_ex_pu_prf,
                    self.penv.d["ef_pu_prf_env_min"][0],
                    self.penv.d["ef_pu_prf_env_max"][0])

                ef_pu_prf_sum = 0

                buf_pass = 1
                while (buf_pass <= 7) & (buf_pass > 0):
                    self.d.loc[buf_pass, "ef_pu_prf_dlt_min"] = mathuty.Max(
                        self.fsstd.lrg.d[buf_pass, "ef_pu_prf_chg_cb"],
                        mathuty.Max(
                            ef_ex_pu_prf,
                            self.penv.d.loc[buf_pass, "ef_pu_prf_env_min"]) -
                        mathuty.Min(
                            ef_en_pu_prf,
                            self.penv.d.loc[buf_pass - 1, "ef_pu_prf_env_max"]))

                    self.d.loc[buf_pass, "ef_pu_prf_dlt_max"] = mathuty.Min(
                        self.fsstd.lrg.d[buf_pass, "ef_pu_prf_chg_we"],
                        mathuty.Min(ef_ex_pu_prf,
                                    self.penv.d.loc[buf_pass, "ef_pu_prf_env_max"]) -
                        mathuty.Max(ef_en_pu_prf,
                                    self.penv.d.loc[buf_pass - 1, "ef_pu_prf_env_min"]))

                    if ef_en_pu_prf <= ef_ex_pu_prf:
                        ef_pu_prf_sum = ef_pu_prf_sum + \
                            self.d.loc[buf_pass, "ef_pu_prf_dlt_max"]

                        if buf_pass == std:
                            if ef_pu_prf_sum <= 0.000001:
                                ef_en_pu_prf = ef_ex_pu_prf
                            else:
                                ef_en_pu_prf = (
                                    ef_ex_pu_prf - self.d.loc[buf_pass, "ef_pu_prf_dlt_max"] *
                                    (ef_ex_pu_prf - ef_en_pu_prf) /
                                    ef_pu_prf_sum)
                        else:
                            if self.penv.d.loc[buf_pass, "ef_pu_prf_env_max"] <= ef_en_pu_prf:
                                ef_en_pu_prf = self.penv.d.loc[buf_pass,
                                                               "ef_pu_prf_env_max"]
                                ef_pu_prf_sum = 0
                            if self.penv.d.loc[buf_pass, "ef_pu_prf_env_min"] >= ef_ex_pu_prf:
                                ef_en_pu_prf = self.penv.d.loc[buf_pass,
                                                               "ef_pu_prf_env_min"]
                                ef_pu_prf_sum = 0
                    else:
                        ef_pu_prf_sum = ef_pu_prf_sum + \
                            self.d.loc[buf_pass, "ef_pu_prf_dlt_min"]

                        if buf_pass == std:
                            if ef_pu_prf_sum >= -0.000001:
                                ef_en_pu_prf = ef_ex_pu_prf
                            else:
                                ef_en_pu_prf = (
                                    ef_ex_pu_prf - self.d.loc[buf_pass, "ef_pu_prf_dlt_min"] *
                                    (ef_ex_pu_prf - ef_en_pu_prf) /
                                    ef_pu_prf_sum)
                        else:
                            if self.penv.d.loc[buf_pass, "ef_pu_prf_env_min"] >= ef_en_pu_prf:
                                ef_en_pu_prf = self.penv.d.loc[buf_pass,
                                                               "ef_pu_prf_env_min"]
                                ef_pu_prf_sum = 0
                            if self.penv.d.loc[buf_pass, "ef_pu_prf_env_max"] <= ef_ex_pu_prf:
                                ef_en_pu_prf = self.penv.d.loc[buf_pass,
                                                               "ef_pu_prf_env_max"]
                                ef_pu_prf_sum = 0

                    if buf_pass == std:
                        break
                    else:
                        buf_pass = buf_pass + 1

                # Calculate initial entry pu profile
                if self.evllpce.d["strn_rlf_cof"][std]
                    self.d.loc[std, "pu_prf_change"] = (
                        1 / self.fsstd.lrg.d.loc[std, "pce_infl_cof"] / pu_prf_change_sum)
                else:
                    self.d.loc[std, "pu_prf_change"] = (
                        self.evllpce.d["strn_rlf_cof"][std] /
                        (self.fsstd.lrg.d.loc[std, "pce_infl_cof"] *
                         self.evllpce.d["elas_modu"][std]) / pu_prf_change_sum)

                ef_en_pu_prf_dft = (
                    ef_ex_pu_prf +
                    (self.targt.d.loc[std, "en_pu_prf"] - self.targt.d.loc[std, "pu_prf"]) *
                    self.d.loc[std, "pu_prf_change"])

                if (((ef_en_pu_prf_dft > ef_ex_pu_prf) & (ef_en_pu_prf_dft < ef_en_pu_prf))
                        | ((ef_en_pu_prf_dft < ef_ex_pu_prf) & (ef_en_pu_prf_dft > ef_en_pu_prf))):
                    ef_en_pu_prf = ef_en_pu_prf_dft

                ef_en_pu_prf = self.targt.Eval_Ef_En_PU_Prf(
                    ef_ex_pu_prf,
                    self.fsstd.lrg.d["ef_pu_prf_chg"][std],
                    self.penv.d["ef_pu_prf_env"][std],
                    ef_en_pu_prf)

        # end of while loop
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

            wr_shft_lim = pd.DataFrame()
            wr_shft_lim["min"] = self.fsstd.d["wr_shft_lim_min"]
            wr_shft_lim["max"] = self.fsstd.d["wr_shft_lim_max"]
            self.fsstd.d[std, "wr_shft"] = self.crlc.Shft_Pos(
                std,
                pce_wr_crn_buf,
                wr_shft_lim,
                self.fsstd.d[std, "wr_shft"])
            pce_wr_crn_buf, wr_br_crn_buf = self.crlc.Crns(
                std, self.fsstd.d[std, "wr_shft"])
        return pce_wr_crn_buf, wr_br_crn_buf

    def actrtyp_bend(self, std, pce_wr_crn, wr_br_crn):
        self.fsstd.d.loc[std, "force_bnd_des"] = self.ufd.Bnd_Frc(
            std,
            self.d["ufd_pu_prf"][std] * self.d["thick"][std],
            self.d["force_pu_wid"][std],
            pce_wr_crn,
            wr_br_crn)
        self.fsstd.d.loc[std, "force_bnd"] = mathuty.Clamp(
            self.fsstd.d["force_bnd_des"],
            self.fsstd.d["force_bnd_lim_min"],
            self.fsstd.d["force_bnd_lim_max"])
