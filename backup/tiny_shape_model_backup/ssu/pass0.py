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

import global_setting as setting
logging.basicConfig(level=logging.INFO, filename="lrg_print.log")


def pass0_calc(enwidth, enthick, *args):

    # interp input
    interp_df = pd.read_csv(
        "{}cfg_crlc/pass0_interp_vec_{}.csv".format(
            setting.CFG_DIR, setting.ROLL_LINE))

    prf_pass0 = np.interp(
        enwidth,
        interp_df["wid_pass0_vec"],
        interp_df["prf_pass0_vec"])

    pu_prf_pass0 = prf_pass0 / enthick
    return prf_pass0, pu_prf_pass0


if __name__ == '__main__':
    cfg = {
        "line": 1580
    }
    enwidth = 1362.94
    enthick = 40.8598
    prf_pass0, pu_prf_pass0 = pass0_calc(enwidth, enthick, cfg)
    print(prf_pass0, pu_prf_pass0)
