# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from lpce import LateralPiece
import global_setting as setting
import logging
logging.basicConfig(level=logging.INFO, filename="print.log")


class LateralRollGap(object):
    """LRG中换算公式约定参数表的顺序"""

    def __init__(self, input_df, lpce_obj):
        # 机架向量准备
        self.std_vec = np.array([1, 2, 3, 4, 5, 6, 7])
        # 输入的dataframe
        self.input_df = input_df
        # lrg object df
        self.df = pd.DataFrame(index=self.std_vec)
        # 准备插值参数
        self.interp_df = pd.read_excel(
            setting.CFG_DIR + "cfg_lrg/lrg_interp_vec.xlsx")
        self.lpce_df = lpce_obj.df
        self.update()

    @staticmethod
    def prf_recv_cof():
        """
        凸度恢复系数 又可称作prf_rlf_cof
        the conversation coefficient
        which represents the ratio of strain relief to profile change.
        """
        return 0.2

    @staticmethod
    def ef_pu_prf_chg(
            bckl_lim,
            pce_infl_cof,
            strn_rlf_cof):
        """
        represents the capability of crown change for stands. The
        available range is calculated as followed
        """
        return (bckl_lim *
                (1 - pce_infl_cof *
                 (1 - (1 - LateralRollGap.prf_recv_cof()) * strn_rlf_cof)
                 ) / pce_infl_cof)

    def update(self):
        """
        --- 更新lrg参数的函数 ---
        """
        # 01 --- pce_infl_cof calcs. / interp manipulation ---
        self.df["wid_thck"] = (
            self.input_df["en_width"] /
            self.input_df["en_thick"])

        self.df["pce_infl_cof"] = [
            np.interp(
                self.df["wid_thck"][std],
                self.interp_df["wid_thck_interp_vec"],
                self.interp_df["pce_infl_cof_interp_vec"])
            for std in self.std_vec]

        # 02 --- ef_pu_prf_chg calcs. ---
        fltIdx_list = ["we", "cb"]
        for flt_idx in fltIdx_list:
            self.df["ef_pu_prf_chg_%s" % flt_idx] = (
                LateralRollGap.ef_pu_prf_chg(
                    self.lpce_df["bckl_lim_%s" % flt_idx],
                    self.df["pce_infl_cof"],
                    self.lpce_df["strn_rlf_cof"])
            )

    def calc(self, std, func_name):
        strn_rlf_cof = self.lpce.df["strn_rlf_cof"][std]
        pce_infl_cof = self.df["pce_infl_cof"][std]
        prf_chg_attn_fac = self.df["prf_chg_attn_fac"][std]

        def Ef_Ex_PU_Prf3(
                ef_en_pu_prf,
                ufd_pu_prf):
            return (
                ef_en_pu_prf +
                (1.0 - pce_infl_cof + (1.0 - LateralRollGap.prf_recv_cof()) *
                 strn_rlf_cof * pce_infl_cof) * (ufd_pu_prf - ef_en_pu_prf) /
                prf_chg_attn_fac)

        def UFD_PU_Prf3(
                ef_en_pu_prf,
                ef_ex_pu_prf):
            scratch = (
                1.0 - pce_infl_cof + (1.0 - LateralRollGap.prf_recv_cof()) *
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

        def Istd_Ex_PU_Prf0(
                std_ex_strn,
                ef_ex_pu_prf):
            """
            calculate interstand exit pu prf for single stand
            """
            return ef_ex_pu_prf + std_ex_strn * (1 - strn_rlf_cof)

        return eval(func_name)
#  --------------------------------------------------------------------------------
#  --------------------------------------------------------------------------------
#  --------------------------------------------------------------------------------
#  --------------------------------------------------------------------------------
#  --------------------------------------------------------------------------------

    def Ef_En_PU_Prf1(
            pce_infl_cof,
            prf_chg_attn_fac,
            ufd_pu_prf,
            std_ex_strn):
        if(0.0 == pce_infl_cof):
            # Infinite effective per unit profile change possible.
            # ef_ex_pu_prf is independet of ef_en_pu_prf
            return ufd_pu_prf
        return ufd_pu_prf - std_ex_strn * prf_chg_attn_fac / pce_infl_cof

    def Ef_En_PU_Prf3(
            strn_rlf_cof,
            pce_infl_cof,
            prf_chg_attn_fac,
            ufd_pu_prf,
            ef_ex_pu_prf,
            ef_en_pu_prf):
        if(0.0 == pce_infl_cof):
            # Infinite effective per unit profile change possible.  Effective exit
            # per unit profile is independent of the effective entry per unit
            # profile.
            return ef_en_pu_prf
        return ((ef_ex_pu_prf * prf_chg_attn_fac -
                 (1.0 - pce_infl_cof + (1.0 - prf_recv_cof()) * pce_infl_cof *
                  strn_rlf_cof) * ufd_pu_prf) /
                (prf_chg_attn_fac -
                 (1.0 - pce_infl_cof + (1.0 - prf_recv_cof()) * pce_infl_cof *
                  strn_rlf_cof)))

    def Std_Ex_Strn1(pce_infl_cof,
                     prf_chg_attn_fac,
                     ef_en_pu_prf,
                     ufd_pu_prf):
        """
        calculate std_ex_strn by ef_en_pu_prf and ufd_pu_prf
        for single stand
        IN pce_infl_cof or pce_infl_cof_vec[std]
        IN prf_chg_attn_fac or prf_chg_attn_fac_vec[std]
        IN ef_en_pu_prf
        IN ufd_pu_prf
        """
        return pce_infl_cof * (ufd_pu_prf - ef_en_pu_prf) / prf_chg_attn_fac


if __name__ == '__main__':

    input_dir = setting.ROOT_DIR + "input_sample/"
    input_df = pd.read_excel(input_dir + "M18001288W_input_sample.xlsx")
    lpce = LateralPiece(input_df)
    lrg = LateralRollGap(input_df, lpce)
    print(lpce.df)
    print(lrg.df)
