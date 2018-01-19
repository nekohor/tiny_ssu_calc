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
logging.basicConfig(level=logging.INFO, filename="lrg_print.log")


def wr_grn_cr(pos_shft, *args, ** kwargs):
    """
    CVC equiv crowm
    """
    # interp cfg parameter
    interp_df = pd.read_excel(
        "cfg_crlc/wr_grn_cr_interp_vec_%d.xlsx" % kwargs["cfg"]["line"]
    )
    # config_file
    profile_df = pd.read_excel(
        "cfg_crlc/profile_df_%d.xlsx" % kwargs["cfg"]["line"]
    )
    rprof = profile_df["rprof"]
    parab_crn = profile_df["parab_crn"]
    # output series
    std_vec = np.array([1, 2, 3, 4, 5, 6, 7])
    cr = pd.Series(index=std_vec)
    for std in std_vec:
        if rprof[std] == "cvc1":
            cr[std] = np.interp(
                pos_shft[std],
                interp_df["cvc_shft_vec"],
                interp_df["cvc_cr_mat_cvc1"]
            )
        elif rprof[std] == "cvc4":
            cr[std] = np.interp(
                pos_shft[std],
                interp_df["cvc_shft_vec"],
                interp_df["cvc_cr_mat_cvc4"]
            )
        else:  # parab including top and bot roll
            cr[std] = parab_crn[std]
    return cr


def Crns(input_df, *args, ** kwargs):
    # 机架向量准备
    pce_wr_cr_buf = (
        input_df["pce_wr_t_cr"] +
        input_df["pce_wr_w_cr"] +
        wr_grn_cr(input_df["pos_shft"], cfg=kwargs["cfg"]) +
        input_df["wr_crn_vrn"] +
        input_df["wr_crn_off"])

    # 支持辊与工作辊长度相对比例系数
    wrbr_df = pd.read_excel(
        "cfg_crlc/wrbr_para_%s.xlsx" % kwargs["cfg"]["line"])
    br_wr_mul = pow(wrbr_df["br"]["length"] / wrbr_df["wr"]["length"], 2)
    wr_br_cr_buf = (
        input_df["br_w_cr"] +
        input_df["wr_br_t_cr"] +
        input_df["wr_br_w_cr"] +
        (   # wr_grn_cr函数调用时加不加cfg都无所谓，因为闭包
            wr_grn_cr(input_df["pos_shft"], cfg) +
            input_df["wr_crn_vrn"] +
            input_df["wr_crn_off"]
        ) * br_wr_mul
    )
    return pce_wr_cr_buf, wr_br_cr_buf


if __name__ == '__main__':
    cfg = {
        "line": 2250
    }
    std_vec = np.array([1, 2, 3, 4, 5, 6, 7])
    pos_shft_array = pd.Series([34, 5, 15, -9, -120, 80, 17])
    pos_shft_array.index = std_vec

    print(wr_grn_cr(pos_shft_array, cfg=cfg))
