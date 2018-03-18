# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import sys
sys.path.append("..")
from scalc.ssu import CompositeRollStackCrown
from scalc.utils import mathuty
import scalc.config.setting as setting


import logging
logging.basicConfig(level=logging.INFO, filename="test_print.log")


# input_df = pd.read_excel(
#     "{}M18001288W_input_sample.xlsx".format(setting.SAMPLE_DIR))
coil_id = "M18025715H"


stk_crn_df = pd.read_excel(
    "{}{}_stack_crown.xlsx".format(setting.SAMPLE_DIR, coil_id))

# env_df = pd.read_excel(
#     "{}{}_env.xlsx".format(setting.SAMPLE_DIR))


crlc = CompositeRollStackCrown(stk_crn_df)

std = 5
pce_wr_cr_req = 0.010005
pce_wr_cr_req = -0.0295831
# pce_wr_cr_req = -0.749592

pce_wr_cr_org = stk_crn_df["pce_wr_cr"][std]

lim_df = pd.DataFrame()
lim_df.loc[std, "pos_shft_lim_min"] = -30
lim_df.loc[std, "pos_shft_lim_max"] = 30


pos_shft_input_vec = range(-140, 140, 1)
# pos_shft_input = -10

pos_result_vec = []
for pos_shft_input in pos_shft_input_vec:
    pos_shift = crlc.Shft_Pos(
        std, pce_wr_cr_req, pce_wr_cr_org, lim_df, pos_shft_input)
    print(pos_shift)
    pos_result_vec.append(pos_shift)
wr_grn_cr = crlc.wr_grn_cr_scalar(std, 0)
print(wr_grn_cr)


plt.plot(pos_shft_input_vec, pos_result_vec)
plt.show()
