# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

import sys
sys.path.append("..")
from scalc.ssu import CompositeRollStackCrown
from scalc.utils import mathuty

import global_setting as setting

import logging
logging.basicConfig(level=logging.INFO, filename="test_print.log")


input_df = pd.read_excel(
    "{}M18001288W_input_sample.xlsx".format(setting.SAMPLE_DIR))

stk_cr_df = pd.read_excel(
    "{}M18001288W_stack_crown.xlsx".format(setting.SAMPLE_DIR))

env_df = pd.read_excel(
    "{}M18001288W_env.xlsx".format(setting.SAMPLE_DIR))


crlc = CompositeRollStackCrown(stk_cr_df)
