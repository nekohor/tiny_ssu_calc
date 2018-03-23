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

# coil_id = "M18001288W"
coil_id = "M18025715H"

input_df = pd.read_excel(
    "{}{}_input_sample.xlsx".format(setting.SAMPLE_DIR, coil_id))
stk_crn_df = pd.read_excel(
    "{}{}_stack_crown.xlsx".format(setting.SAMPLE_DIR, coil_id))

# env_df = pd.read_excel(
#     "{}{}_env.xlsx".format(setting.SAMPLE_DIR))


crlc = CompositeRollStackCrown(input_df, stk_crn_df)


print(crlc.crlc_df)

print(crlc.wr_grn_cr_vector(input_df["pos_shft"]))
print(crlc.Crns_vector(input_df["pos_shft"]))
