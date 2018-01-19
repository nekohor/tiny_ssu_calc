# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib
from dateutil.parser import parse
from datetime import datetime
import seaborn as sns
import os
import sys
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
import logging
import lpce
logging.basicConfig(level=logging.INFO, filename="print.log")


def Ef_En_PU_Prf1(
        pce_infl_cof,
        prf_chg_attn_fac,
        ufd_pu_prf,
        std_ex_strn):
    if(0.0 == pce_infl_cof):
        # Infinite effective per unit profile change possible.  Effective exit
        # per unit profile is independent of the effective entry per unit
        # profile.
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


def UFD_PU_Prf3(
        strn_rlf_cof,
        pce_infl_cof,
        prf_chg_attn_fac,
        ef_en_pu_prf,
        ef_ex_pu_prf):
    scratch = (1.0 - pce_infl_cof + (1.0 - prf_recv_cof()) * strn_rlf_cof *
               pce_infl_cof)

    if 0.0 == scratch:
        # // -----------------------------------------------------------------
        # // It is impossible to change the effective per unit profile if the
        # // differential strain relief coefficient yields zero and the piece
        # // influence coefficient yields one.
        # // -----------------------------------------------------------------
        return ef_ex_pu_prf
    return (ef_en_pu_prf +
            (ef_ex_pu_prf - ef_en_pu_prf) * prf_chg_attn_fac / scratch)


def Istd_Ex_PU_Prf0(strn_rlf_cof,
                    std_ex_strn,
                    ef_ex_pu_prf):
    """
    calculate interstand exit pu prf for single stand
    IN strn_rlf_cof or strn_rlf_cof_vec[std]
    IN std_ex_strn
    IN ef_ex_pu_prf
    """
    return ef_ex_pu_prf + std_ex_strn * (1 - strn_rlf_cof)


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


def prf_recv_cof():
    """
    凸度恢复系数 又可称作prf_rlf_cof
    the conversation coefficient
    which represents the ratio of strain relief to profile change.
    """
    return 0.2


def ef_pu_prf_chg(
        bckl_lim,
        pce_infl_cof,
        strn_rlf_cof):
    """
    represents the capability of crown change for stands. The
    available range is calculated as followed
    """
    return (bckl_lim *
            (1 - pce_infl_cof * (1 - (1 - prf_recv_cof()) * strn_rlf_cof)) /
            pce_infl_cof
            )


def update(input_df, lpce_df, *args):
    """
    --- 更新lrg参数的函数 ---
    """
    # 准备
    std_vec = np.array([1, 2, 3, 4, 5, 6, 7])

    # updated lrg object df
    output_df = pd.DataFrame(index=std_vec)

    # 01 --- pce_infl_cof calcs. / interp manipulation ---

    # 准备interp参数
    interp_df = pd.read_excel("cfg_lrg/lrg_interp_vec.xlsx")

    output_df["wid_thck"] = (input_df["pcEnPceD_width"] /
                             input_df["pcEnPceD_thick"])

    output_df["pce_infl_cof"] = [np.interp(
        output_df["wid_thck"][std],
        interp_df["wid_thck_interp_vec"],
        interp_df["pce_infl_cof_interp_vec"])
        for std in std_vec]

    # 02 --- ef_pu_prf_chg calcs. ---
    fltIdx_list = ["we", "cb"]
    for flt_idx in fltIdx_list:
        output_df["ef_pu_prf_chg_%s" % flt_idx] = (
            ef_pu_prf_chg(
                lpce_df["bckl_lim_%s" % flt_idx],
                output_df["pce_infl_cof"],
                lpce_df["strn_rlf_cof"])
        )

    return output_df


if __name__ == '__main__':
    cfg_dict = {
        "line": 1580
    }
    input_dir = "input_sample/"
    input_df = pd.read_excel(input_dir + "M18001288W_input_sample.xlsx")
    lpce_df = lpce.update(input_df, cfg_dict)
    print(lpce_df)
    lrg_df = update(input_df, lpce_df)
    print(lrg_df)
