# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from config.setting import CFG_DIR
import logging
logging.basicConfig(level=logging.INFO, filename="lrg_print.log")


class LateralRollGap(object):
    """LRG中换算公式约定参数表的顺序"""

    def __init__(self, fsstd, lpce):
        # 机架向量准备
        self.std_vec = np.array([1, 2, 3, 4, 5, 6, 7])
        # 输入的dataframe
        self.fsstd = fsstd
        # lrg object df
        self.d = pd.DataFrame(index=self.std_vec)
        # 准备插值参数

        self.interp_df = pd.read_excel(CFG_DIR + "/cfg_lrg/lrg_interp.xlsx")
        self.lpce = lpce
        self.update()

    def prf_recv_cof(self):
        """
        凸度恢复系数 又可称作prf_rlf_cof
        the conversation coefficient
        which represents the ratio of strain relief to profile change.
        """
        return 0.2

    def ef_pu_prf_chg(
            self,
            bckl_lim,
            pce_infl_cof,
            strn_rlf_cof):
        """
        represents the capability of crown change for stands. The
        available range is calculated as followed
        """
        return (bckl_lim *
                (1 - pce_infl_cof *
                 (1 - (1 - self.prf_recv_cof()) * strn_rlf_cof)
                 ) / pce_infl_cof)

    # def prf_chng_attn_fac(
    #     ...
    # ):
    #     drft = input_df["en_thick"] - input_df["ex_thick"]
    #     kgpt_lbpt_npkn = 1000

    def update(self):
        """
        --- 更新lrg参数的函数 ---
        """
        # 01 --- pce_infl_cof calcs. / interp manipulation ---
        self.d["wid_thck"] = (
            self.fsstd.d["en_width"] /
            self.fsstd.d["en_thick"])

        self.d["pce_infl_cof"] = [
            np.interp(
                self.d["wid_thck"][std],
                self.interp_df["wid_thck_interp_vec"],
                self.interp_df["pce_infl_cof_interp_vec"])
            for std in self.std_vec]

        # 02 --- ef_pu_prf_chg calcs. ---
        fltIdx_list = ["we", "cb"]
        for flt_idx in fltIdx_list:
            self.d["ef_pu_prf_chg_%s" % flt_idx] = (
                self.ef_pu_prf_chg(
                    self.lpce.d["bckl_lim_%s" % flt_idx],
                    self.d["pce_infl_cof"],
                    self.lpce.d["strn_rlf_cof"])
            )

        # 03 --- 凸度削弱因子的计算prf_chg_attn_fac ---
        # 太繁琐了，直接从SSU里取
        # 真要实现,需要找hitchcock和hitchterm再计算lrg::prf_chg_attn_fac
        self.d["prf_chg_attn_fac"] = self.fsstd.d["prf_chg_attn_fac"]

    def calc(self, std, func_name):
        prf_recv_cof = self.prf_recv_cof()
        strn_rlf_cof = self.lpce.d["strn_rlf_cof"][std]
        pce_infl_cof = self.d["pce_infl_cof"][std]
        prf_chg_attn_fac = self.d["prf_chg_attn_fac"][std]

        def Ef_En_PU_Prf1(
                ufd_pu_prf,
                std_ex_strn):
            if 0 == pce_infl_cof:
                return ufd_pu_prf
            return (ufd_pu_prf - std_ex_strn * prf_chg_attn_fac / pce_infl_cof)

        def Ef_En_PU_Prf3(
                ufd_pu_prf,
                ef_ex_pu_prf,
                ef_en_pu_prf):
            if 0 == pce_infl_cof:
                return ef_en_pu_prf
            return (
                ef_ex_pu_prf * prf_chg_attn_fac -
                (1 - pce_infl_cof + (1 - prf_recv_cof) * pce_infl_cof *
                    strn_rlf_cof) * ufd_pu_prf) / (prf_chg_attn_fac - (
                        1 - pce_infl_cof + (1 - prf_recv_cof) * pce_infl_cof *
                        strn_rlf_cof))

        def Ef_En_PU_Prf5(
                std_ex_strn,
                istd_ex_pu_prf):
            if 0 == pce_infl_cof:
                return istd_ex_pu_prf
            return(
                istd_ex_pu_prf - (1.0 - prf_recv_cof * strn_rlf_cof *
                                  pce_infl_cof) * std_ex_strn / pce_infl_cof)

        def Ef_Ex_PU_Prf3(
                ef_en_pu_prf,
                ufd_pu_prf):
            return (
                ef_en_pu_prf +
                (1.0 - pce_infl_cof + (1.0 - prf_recv_cof) *
                 strn_rlf_cof * pce_infl_cof) * (ufd_pu_prf - ef_en_pu_prf) /
                prf_chg_attn_fac)

        def UFD_PU_Prf1(
                ef_en_pu_prf,
                std_ex_strn):
            if 0 == pce_infl_cof:
                return ef_en_pu_prf
            return ef_en_pu_prf + std_ex_strn * prf_chg_attn_fac / pce_infl_cof

        def UFD_PU_Prf3(
                ef_en_pu_prf,
                ef_ex_pu_prf):
            scratch = (
                1.0 - pce_infl_cof + (1.0 - prf_recv_cof) *
                strn_rlf_cof * pce_infl_cof)

            if 0.0 == scratch:
                # ------------------------------------------------------
                # It is impossible to change the ef_pu_prf if the
                # strain relief coefficient yields zero and the piece
                # influence coefficient yields one.
                # ------------------------------------------------------
                return ef_ex_pu_prf
            return (ef_en_pu_prf +
                    (ef_ex_pu_prf - ef_en_pu_prf) * prf_chg_attn_fac / scratch)

        def Std_Ex_Strn1(
                ef_en_pu_prf,
                ufd_pu_prf):
            return (
                pce_infl_cof * (ufd_pu_prf - ef_en_pu_prf) / prf_chg_attn_fac)

        def Std_Ex_Strn5(
                ef_en_pu_prf,
                istd_ex_pu_prf):
            return (
                pce_infl_cof * (istd_ex_pu_prf - ef_en_pu_prf) /
                (1.0 - prf_recv_cof * strn_rlf_cof * pce_infl_cof))

        def Std_Ex_Strn6(
                ufd_pu_prf,
                istd_ex_pu_prf):
            if 0 == pce_infl_cof:
                return 0
            return (
                pce_infl_cof * (ufd_pu_prf - istd_ex_pu_prf) /
                (prf_chg_attn_fac -
                    1.0 + prf_recv_cof * strn_rlf_cof * pce_infl_cof))

        def Istd_Ex_Strn2(std_ex_strn):
            return std_ex_strn * (1.0 - strn_rlf_cof)

        def Istd_Ex_PU_Prf0(
                std_ex_strn,
                ef_ex_pu_prf):
            """
            calculate interstand exit pu prf for single stand
            """
            return ef_ex_pu_prf + std_ex_strn * (1 - strn_rlf_cof)

        return eval(func_name)
