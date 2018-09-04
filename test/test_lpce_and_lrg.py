# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import sys
sys.path.append("..")
# from scalc.ssu import CompositeRollStackCrown
from scalc.utils import mathuty
import scalc.config.setting as setting

from scalc.ssu import LateralPiece
from scalc.ssu import LateralRollGap
from scalc.ssu import UniForcDist
from scalc.ssu import CompositeRollStackCrown
import logging
logging.basicConfig(level=logging.INFO, filename="test_print.log")

coil_id = "M18001288W"
# coil_id = "M18025715H"
# coil_id = "H17177777L"

input_df = pd.read_excel(
    "{}{}_input_sample.xlsx".format(setting.SAMPLE_DIR, coil_id))
stk_crn_df = pd.read_excel(
    "{}{}_stack_crown.xlsx".format(setting.SAMPLE_DIR, coil_id))

# env_df = pd.read_excel(
#     "{}{}_env.xlsx".format(setting.SAMPLE_DIR))

lpce = LateralPiece(input_df)
lrg = LateralRollGap(input_df, lpce)

print(lpce.df)
print(lrg.df)
