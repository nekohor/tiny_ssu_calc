# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from lpce import LateralPiece
from lrg import LateralRollGap
from ufd import UniForcDist
from crlc import CompositeRollStackCrown

import mathuty
import global_setting as setting

input_df = pd.read_excel(
    "{}M18001288W_input_sample.xlsx".format(setting.SAMPLE_DIR))

stk_cr_df = pd.read_excel(
    "{}M18001288W_stack_crown.xlsx".format(setting.SAMPLE_DIR))

env_df = pd.read_excel(
    "{}M18001288W_env.xlsx".format(setting.SAMPLE_DIR))

ufd = UniForcDist(input_df)
lpce = LateralPiece(input_df)
lrg = LateralRollGap(input_df, lpce)
crlc = CompositeRollStackCrown(stk_cr_df)


std = 1
print("ef_pu_prf_env_min:", std)
print(lrg.calc(std, "Ef_Ex_PU_Prf3")(
    env_df["ef_pu_prf_env_min"][std - 1],
    env_df["ufd_pu_prf_env_min"][std]))
