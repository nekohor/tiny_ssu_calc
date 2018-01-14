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


def wr_grn_cr(cfg, pos_shft):
    """
    CVC equiv crowm
    """
    # interp cfg parameter
    interp_df = pd.read_excel(
        "cfg_crlc/wr_grn_cr_interp_vec_%d.xlsx" % cfg["line"]
    )
    # config_file
    profile_df = pd.read_excel(
        "cfg_crlc/profile_df_%d.xlsx" % cfg["line"]
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


def Crns(t_w_cr_df, input_df):
    # 机架向量准备
    std_vec = np.array([1, 2, 3, 4, 5, 6, 7])


if __name__ == '__main__':
    cfg = {
        "line": 2250
    }
    std_vec = np.array([1, 2, 3, 4, 5, 6, 7])
    pos_shft_array = pd.Series([34, 5, 15, -9, -120, 80, 17])
    pos_shft_array.index = std_vec

    print(wr_grn_cr(cfg, pos_shft_array))
