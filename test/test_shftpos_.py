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


coil_id = "M18001288W"
# coil_id = "M18025715H"
# coil_id = "M18025704H"

input_df = pd.read_excel(
    "{}{}_input_sample.xlsx".format(setting.SAMPLE_DIR, coil_id))
stk_crn_df = pd.read_excel(
    "{}{}_stack_crown.xlsx".format(setting.SAMPLE_DIR, coil_id))

# env_df = pd.read_excel(
#     "{}{}_env.xlsx".format(setting.SAMPLE_DIR))


crlc = CompositeRollStackCrown(input_df, stk_crn_df)

std = 5
pce_wr_cr_req = 0.010005
pce_wr_cr_req = -0.0295831   # M18025715H  F5   cf
pce_wr_cr_req = 0.0331397   # M18025704H  F5   c0
pce_wr_cr_req = -0.03   # M18001288W  F5   c0
# pce_wr_cr_req = -0.749592

# pce_wr_cr_org = stk_crn_df["pce_wr_cr"][std]
pce_wr_cr_org, wr_br_crn_org = crlc.Crns(std, 0)
# pce_wr_cr_org = -0.9
print("hehe", pce_wr_cr_org)

lim_df = pd.DataFrame()
lim_df.loc[std, "pos_shft_lim_min"] = -140
lim_df.loc[std, "pos_shft_lim_max"] = -91


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
