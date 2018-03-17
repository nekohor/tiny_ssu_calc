# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

import sys
sys.path.append("..")
from scalc.ssu import CompositeRollStackCrown
from scalc.utils import mathuty
import scalc.config.setting as setting


import logging
logging.basicConfig(level=logging.INFO, filename="test_print.log")


# input_df = pd.read_excel(
#     "{}M18001288W_input_sample.xlsx".format(setting.SAMPLE_DIR))

stk_crn_df = pd.read_excel(
    "{}M18025703H_stack_crown.xlsx".format(setting.SAMPLE_DIR))

env_df = pd.read_excel(
    "{}M18001288W_env.xlsx".format(setting.SAMPLE_DIR))


crlc = CompositeRollStackCrown(stk_crn_df)

std = 5
pce_wr_cr_req = 0.010005
pce_wr_cr_org = stk_crn_df["pce_wr_cr"][std]

lim_df = pd.DataFrame()
lim_df.loc[std, "pos_shft_lim_min"] = -87.96
lim_df.loc[std, "pos_shft_lim_max"] = 2.07

pos_shft_input = 140
pos_shift = crlc.Shft_Pos(
    std, pce_wr_cr_req, pce_wr_cr_org, lim_df, pos_shft_input)
print(pos_shift)
