from utils import mathuty
from config.setting import LOG_DIR
import logging
logging.basicConfig(level=logging.INFO, filename=LOG_DIR + "/print.log")


class Target():

    def __init__(self, fsstd, lpce, lrg, ufd, crlc, penv, alc):
        self.fsstd = fsstd
        self.lpce = lpce
        self.lrg = lrg
        self.ufd = ufd
        self.crlc = crlc

        self.penv = penv
        self.alc = alc
        self.std_vec = [1, 2, 3, 4, 5, 6, 7]
        self.Init()

    def Init(self):
        self.en_pu_prf = self.fsstd.d["pu_prf_pass0"].mean()
        print("en_pu_prf", self.en_pu_prf)

        # prf_int定点于targt.cxx的493行
        self.prf_int = self.fsstd.d["prf_int"].mean()
        self.pce_thck = self.fsstd.d["ex_thick"][7]

        self.pu_prf = self.prf_int / self.pce_thck

        self.pu_prf_tgt = self.prf_int / self.pce_thck
        self.pu_prf_old = self.prf_int / self.pce_thck

        self.prf_tol_min = -0.005
        self.prf_tol_max = 0.005

        self.pu_prf_lim_min = (self.prf_int + self.prf_tol_min) / self.pce_thck
        self.pu_prf_lim_max = (self.prf_int + self.prf_tol_max) / self.pce_thck
        print("pu_prf_lim min/max", self.pu_prf_lim_min, self.pu_prf_lim_max)

    def Delvry_Pass(self):
        print("========================Delvry_Pass start=====================")
        self.pu_prf = mathuty.Clamp(
            self.pu_prf_tgt,
            self.penv.d["pu_prf_env_min"][7],
            self.penv.d["pu_prf_env_max"][7]
        )
        print("pu_prf")
        print(self.pu_prf)

        # bspare = self.Limit_PU_Prf(self.pu_prf)

        self.ef_en_pu_prf = self.pu_prf
        for std in self.std_vec[:-1]:
            self.ef_en_pu_prf = mathuty.Clamp(
                self.ef_en_pu_prf,
                self.penv.d["ef_pu_prf_env_min"][std],
                self.penv.d["ef_pu_prf_env_max"][std]
            )

        self.std_ex_strn_buf = self.lrg.calc(7, "Std_Ex_Strn5")(
            self.ef_en_pu_prf, self.pu_prf)
        self.std_ex_strn = mathuty.Clamp(
            self.std_ex_strn_buf,
            self.lpce.d["crit_bckl_lim_cb"][7],
            self.lpce.d["crit_bckl_lim_we"][7])
        print("std_ex_strn")
        print(self.std_ex_strn)

        if self.std_ex_strn_buf != self.std_ex_strn:
            self.ef_en_pu_prf = self.lrg.calc(7, "Ef_En_PU_Prf5")(
                self.std_ex_strn, self.pu_prf)

        self.ufd_pu_prf_buf = self.lrg.calc(7, "UFD_PU_Prf1")(
            self.ef_en_pu_prf, self.std_ex_strn)
        self.ufd_pu_prf = mathuty.Clamp(
            self.ufd_pu_prf_buf,
            self.penv.d["ufd_pu_prf_env_min"][7],
            self.penv.d["ufd_pu_prf_env_max"][7]
        )
        print("ufd_pu_prf_buf", self.ufd_pu_prf_buf)
        print("ufd_pu_prf", self.ufd_pu_prf)

        if self.ufd_pu_prf_buf != self.ufd_pu_prf:
            self.std_ex_strn = self.lrg.calc(7, "Std_Ex_Strn6")(
                self.ufd_pu_prf, self.pu_prf)
            self.ef_en_pu_prf = self.lrg.calc(7, "Ef_En_PU_Prf1")(
                self.ufd_pu_prf, self.std_ex_strn)

        self.ef_ex_pu_prf = self.lrg.calc(7, "Ef_Ex_PU_Prf3")(
            self.ef_en_pu_prf, self.ufd_pu_prf)

        self.istd_ex_strn = self.lrg.calc(7, "Istd_Ex_Strn2")(
            self.std_ex_strn)
        print("ef_en_pu_prf", self.ef_en_pu_prf)
        print("ef_ex_pu_prf", self.ef_ex_pu_prf)
        print("istd_ex_strn", self.istd_ex_strn)
        print("======================Delvry_Pass end========================")
        return self.ef_en_pu_prf, self.ef_ex_pu_prf, self.istd_ex_strn

    def Pass_Mill_Targ(self, std):
        ef_en_pu_prf = 0
        ef_pu_prf_buf = 0
        std_ex_strn = 0
        std_ex_strn_buf = 0
        ufd_pu_prf = 0

        ufd_pu_prf = self.ufd.Prf(
            std,
            self.alc.d["force_pu_wid"][std],
            self.fsstd.d["force_bnd"][std],
            self.crlc.d["pce_wr_cr"][std],
            self.crlc.d["wr_br_cr"][std]) / self.alc.d["thick"][std]

        ef_pu_prf = self.Ef_PU_Prf_Aim(std)

        ef_en_pu_prf = self.lrg.calc(std, "Ef_En_PU_Prf3")(
            ufd_pu_prf, ef_pu_prf, 0)
        ef_en_pu_prf = mathuty.Clamp(
            ef_en_pu_prf,
            self.penv.d["ef_pu_prf_env_min"][std - 1],
            self.penv.d["ef_pu_prf_env_max"][std - 1])

        std_ex_strn_buf = self.lrg.calc(std, "Std_Ex_Strn1")(
            ef_en_pu_prf, ufd_pu_prf)
        std_ex_strn = mathuty.Clamp(
            std_ex_strn_buf,
            self.lpce.d["crit_bckl_lim_cb"][std],
            self.lpce.d["crit_bckl_lim_we"][std])

        if std_ex_strn != std_ex_strn_buf:
            ef_en_pu_prf = self.lrg.calc(std, "Ef_En_PU_Prf1")(
                ufd_pu_prf, std_ex_strn)

            ef_pu_prf = self.lrg.calc(std, "Ef_Ex_PU_Prf3")(
                ef_en_pu_prf, ufd_pu_prf)

        ef_pu_prf = mathuty.Clamp(
            ef_pu_prf,
            self.penv.d["ef_pu_prf_env_min"][std],
            self.penv.d["ef_pu_prf_env_max"][std])

        while std != 7 & std >= 0:
            std = std + 1

            ef_pu_prf_buf = self.Ef_PU_Prf_Aim(std)

            if ef_pu_prf > ef_pu_prf_buf:
                ef_pu_prf = ef_pu_prf + self.lrg.d["ef_pu_prf_chg_cb"][std]
                ef_pu_prf = max(ef_pu_prf, ef_pu_prf_buf)
            else:
                ef_pu_prf = ef_pu_prf + self.lrg.d["ef_pu_prf_chg_we"][std]
                ef_pu_prf = min(ef_pu_prf, ef_pu_prf_buf)

            ef_pu_prf = mathuty.Clamp(
                ef_pu_prf,
                self.penv.d["ef_pu_prf_env_min"][std],
                self.penv.d["ef_pu_prf_env_max"][std])

        return ef_pu_prf

    def Ef_PU_Prf_Aim(self, std):
        ef_pu_prf_buf = 0
        ef_pu_prf_buf = self.pu_prf - self.istd_ex_strn

        buf_pass = 7
        while buf_pass >= 1 & buf_pass <= 7:
            ef_pu_prf_buf = mathuty.Clamp(
                ef_pu_prf_buf,
                self.penv.d["ef_pu_prf_env_min"][buf_pass],
                self.penv.d["ef_pu_prf_env_max"][buf_pass])

            if buf_pass == std:
                break
            else:
                buf_pass = buf_pass - 1
        return ef_pu_prf_buf

    def Limit_PU_Prf(self, pu_prf_buf):
        self.pu_prf = mathuty.Clamp(
            pu_prf_buf,
            self.pu_prf_lim_min,
            self.pu_prf_lim_max)

        self.targ_same = self.pu_prf == self.pu_prf_old
        self.pu_prf_old = self.pu_prf
        return self.targ_same

    def Eval_Ef_En_PU_Prf(
            self,
            ef_ex_pu_prf,
            ef_pu_prf_chg_cb,
            ef_pu_prf_chg_we,
            ef_pu_prf_env_min,
            ef_pu_prf_env_max,
            ef_en_pu_prf):
        self.ef_en_pu_prf = mathuty.Clamp(
            ef_en_pu_prf,
            ef_pu_prf_env_min,
            ef_pu_prf_env_max)

        if (self.ef_en_pu_prf + ef_pu_prf_chg_we) < ef_ex_pu_prf:
            self.ef_en_pu_prf = ef_ex_pu_prf - ef_pu_prf_chg_we
        elif (self.ef_en_pu_prf + ef_pu_prf_chg_cb) > ef_ex_pu_prf:
            self.ef_en_pu_prf = ef_ex_pu_prf - ef_pu_prf_chg_cb

        return self.ef_en_pu_prf
