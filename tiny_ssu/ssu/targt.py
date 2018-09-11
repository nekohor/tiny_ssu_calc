from utils import mathuty


class Target():

    def __init__(self, fsstd, lpce, lrg, penv):
        self.fsstd = fsstd
        self.lpce = lpce
        self.lrg = lrg
        self.penv = penv

        self.std_vec = [1, 2, 3, 4, 5, 6, 7]
        self.Init()

    def Init(self):
        # prf_int定点于targt.cxx的493行
        self.prf_int = self.fsstd.d["prf_int"].mean()
        self.pce_thck = self.fsstd.d["ex_thick"][7]

        self.pu_prf = self.prf_int / self.pce_thck
        self.pu_prf_tgt = self.prf_int / self.pce_thck
        self.pu_prf_old = self.prf_int / self.pce_thck

    def Delvry_Pass(self):
        self.pu_prf = mathuty.Clamp(
            self.pu_prf_tgt,
            self.penv.d["pu_prf_env_min"][7],
            self.penv.d["pu_prf_env_max"][7]
        )

        # Limit_PU_Prf( pu_prf, bspare );

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
            self.lpce.d["crit_bckl_lim_we"][7]
        )
        if self.std_ex_strn_buf != self.std_ex_strn:
            self.ef_en_pu_prf = self.lrg.calc(7, "Ef_En_PU_Prf5")(
                self.std_ex_strn, self.pu_prf)

        self.ufd_pu_prf_buf = self.lrg.calc(7, "UFD_PU_Prf1")(
            self.ef_en_pu_prf, self.std_ex_strn)
        self.ufd_pu_prf = mathuty.Clamp(
            self.ufd_pu_prf_buf,
            self.penv.d["ufd_pu_prf_env_max"][std],
            self.penv.d["ufd_pu_prf_env_max"][std]
        )
        if self.ufd_pu_prf_buf != self.ufd_pu_prf:
            self.std_ex_strn = self.lrg.calc(7, "Std_Ex_Strn6")(
                self.ufd_pu_prf, self.pu_prf)
            self.ef_en_pu_prf = self.lrg.calc(7, "Ef_En_PU_Prf1")(
                self.ufd_pu_prf, self.std_ex_strn)

        self.ef_ex_pu_prf = self.lrg.calc(7, "Ef_Ex_PU_Prf3")(
            self.ef_en_pu_prf, self.ufd_pu_prf)

        self.istd_ex_strn = self.lrg.calc(7, "Istd_Ex_Strn2")(
            self.std_ex_strn)

        return self.ef_en_pu_prf, self.ef_ex_pu_prf, self.istd_ex_strn
