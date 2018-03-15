# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

import sys
sys.path.append("C:/digestion/tiny_ssu_calc")
from ssu.lpce import LateralPiece
from ssu.lrg import LateralRollGap
from ssu.ufd import UniForcDist
from ssu.crlc import CompositeRollStackCrown

import os
import ssu.mathuty as mathuty
import global_setting as setting

import logging
logging.basicConfig(level=logging.INFO, filename="test_print.log")


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


# --- Ef_Ex_PU_Prf3计算ef_pu_prf无问题
# std = 2
# print("ef_pu_prf_env_min:", std)
# print(lrg.calc(std, "Ef_Ex_PU_Prf3")(
#     env_df["ef_pu_prf_env_min"][std - 1],
#     env_df["ufd_pu_prf_env_min"][std]))

# std_vec = np.array([1, 2, 3, 4, 5, 6, 7])
# for m__ in ["min", "max"]:
#     for std in std_vec:
#         env_df.loc[std, "ufd_pu_prf_env_{}".format(m__)] = (
#             ufd.Prf(
#                 std,
#                 env_df["force_pu_wid_env_{}".format(m__)][std],
#                 env_df["force_bnd_env_{}".format(m__)][std],
#                 env_df["pce_wr_crn_env_{}".format(m__)][std],
#                 env_df["wr_br_crn_env_{}".format(m__)][std]) /
#             input_df["ex_thick"][std])

std = 1
while std > 0:
    mxx_list = ["max", "min"]
    for m__ in mxx_list:
        env_df.loc[std, "ufd_pu_prf_env_{}".format(m__)] = (
            ufd.Prf(
                std,
                env_df["force_pu_wid_env_{}".format(m__)][std],
                env_df["force_bnd_env_{}".format(m__)][std],
                env_df["pce_wr_crn_env_{}".format(m__)][std],
                env_df["wr_br_crn_env_{}".format(m__)][std]) /
            input_df["ex_thick"][std])

    # pu_prf_env计算的验证无问题
    # env_df.loc[std, "ef_pu_prf_env_{}".format(m__)] = (
    #     lrg.calc(std, "Ef_Ex_PU_Prf3")(
    #         env_df["ef_pu_prf_env_{}".format(m__)][std - 1],
    #         env_df["ufd_pu_prf_env_{}".format(m__)][std]))

    # std_ex_strn = lrg.calc(std, "Std_Ex_Strn1")(
    #     env_df["ef_pu_prf_env_{}".format(m__)][std],
    #     env_df["ufd_pu_prf_env_{}".format(m__)][std])

    # # 计算比例凸度包络线上下限
    # env_df.loc[std, "pu_prf_env_{}".format(m__)] = (
    #     lrg.calc(std, "Istd_Ex_PU_Prf0")(
    #         std_ex_strn,
    #         env_df["ef_pu_prf_env_{}".format(m__)][std]))
    # 迭代计数器处理
    if 7 == std:
        break
    else:
        std = std + 1

logging.info(env_df)
logging.info(env_df["ufd_pu_prf_env_min"])
logging.info(env_df["ufd_pu_prf_env_max"])

# logging.info(env_df)
# logging.info(env_df["ufd_pu_prf_env_min"])
# logging.info(env_df["ufd_pu_prf_env_max"])
