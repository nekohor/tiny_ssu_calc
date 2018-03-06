# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from lpce import LateralPiece
from lrg import LateralRollGap
from ufd import UniForcDist
import crlc

import mathuty
import global_setting as setting
import logging
logging.basicConfig(level=logging.INFO, filename="lrg_print.log")


class Envelope():
    def __init__(self):
        self.std_vec = np.array([1, 2, 3, 4, 5, 67])


std_vec = np.array([0, 1, 2, 3, 4, 5, 67])

input_df = None

ufd = UniForcDist(input_df)
lpce = LateralPiece(input_df)
lrg = LateralRollGap(input_df, lpce)


# lim_nom dataframe
lim_df = pd.read_excel(
    "{}cfg_env/std_{}.xlsx".format(setting.CFG_DIR, setting.ROLL_LINE))

posmin = lim_df["wr_shft_lim_min"]
posmax = lim_df["wr_shft_lim_max"]

# 计算辊系凸度
lim_df["pce_wr_crn_lim_min"], lim_df["wr_br_crn_lim_min"] = crlc.Crns(posmin)
lim_df["pce_wr_crn_lim_max"], lim_df["wr_br_crn_lim_max"] = crlc.Crns(posmax)

# 计算单位轧制力
input_df["force_pu_wid"] = input_df["rolling_force"] / input_df["en_width"]
lim_df["force_pu_wid_lim_min"] = input_df["force_pu_wid"]
lim_df["force_pu_wid_lim_max"] = input_df["force_pu_wid"]

# nom窜辊位辊系凸度
posnom = lim_df["wr_shft_nom"]
lim_df["pce_wr_crn_nom"], lim_df["wr_br_crn_lim_nom"] = crlc.Crns(posnom)

# lim的max/min与env中的min/max对应上
env_df = pd.DataFrame(index=std_vec)
env_df["force_bnd_env_min"] = lim_df["force_bnd_lim_max"]
env_df["force_bnd_env_max"] = lim_df["force_bnd_lim_min"]

env_df["pos_shft_env_min"] = lim_df["wr_shft_lim_max"]
env_df["pos_shft_env_max"] = lim_df["wr_shft_lim_min"]

env_df["force_pu_wid_env_min"] = lim_df["force_pu_wid_lim_min"]
env_df["force_pu_wid_env_max"] = lim_df["force_pu_wid_lim_max"]

env_df["pce_wr_crn_env_min"] = lim_df["pce_wr_crn_lim_max"]
env_df["pce_wr_crn_env_max"] = lim_df["pce_wr_crn_lim_min"]

env_df["wr_br_crn_env_min"] = ["wr_br_crn_lim_max"]
env_df["wr_br_crn_env_max"] = ["wr_br_crn_lim_min"]


for m__ in ["min", "max"]:

    fpwenv = env_df["force_pu_wid_env_{}".format(m__)]
    fbenv = env_df["force_bnd_env_{}".format(m__)]
    pwcenv = env_df["pce_wr_crn_env_{}".format(m__)]
    wbcenv = env_df["wr_br_crn_env_{}".format(m__)]

    env_df["ufd_pu_prf_env_{}".format(m__)] = (
        ufd.Prf(fpwenv, fbenv, pwcenv, wbcenv) / input_df["ex_thick"]
    )


bckl_list = ["we", "cb"]
for bckl in bckl_list:
    lim_df["std_ex_strn_lim_{}".format(bckl)] = (
        lpce.df["bckl_lim_{}".format(bckl)])


# 计算各机架入口有效单位凸度极限范围
# 后期用cLRGD::Ef_En_PU_Prf1(..)替换这个计算过程
for std in std_vec:
    lim_df.loc[std - 1, "ef_pu_prf_lim_min"] = (
        lim_df.loc[std, "ufd_pu_prf_env_min"] -
        lim_df.loc[std, "std_ex_strn_lim_we"] *
        lrg.df.loc[std, "prf_chg_attn_fac"] / lrg.df.loc[std, "pce_infl_cof"])

    lim_df.loc[std - 1, "ef_pu_prf_lim_max"] = (
        lim_df.loc[std, "ufd_pu_prf_env_max"] -
        lim_df.loc[std, "std_ex_strn_lim_cb"] *
        lrg.df.loc[std, "prf_chg_attn_fac"] / lrg.df.loc[std, "pce_infl_cof"])
    if std == 7:
        lim_df.loc[std, "ef_pu_prf_lim_min"] = -1
        lim_df.loc[std, "ef_pu_prf_lim_max"] = 1

# mean指的意思是都一样的
env_df.loc[0, "ef_pu_prf_env_min"] = input_df["pu_prf_pass0"].mean()
env_df.loc[0, "ef_pu_prf_env_max"] = input_df["pu_prf_pass0"].mean()

# 包络线对应的极限机架号
pas_env_lim_min = 0
pas_env_lim_max = 0

# ========================= 协调单位凸度包络线 ===================================
std = 1
while std > 0:
    move_prv_min = False
    # 计算各机架出口有效单位凸度包络线下限
    eppenv = env_df["ef_pu_prf_env_min"][std - 1]
    uppenv = env_df["ufd_pu_prf_env_min"][std]
    env_df.loc[std, "ef_pu_prf_env_min"] = lrg.calc(
        std, "Ef_Ex_PU_Prf3")(eppenv, uppenv)

    # 若出口有效单位凸度包络线下限小于极限值下限，修正出口有效单位凸度包络线下限
    if env_df["ef_pu_prf_env_min"][std] < lim_df["ef_pu_prf_lim_min"][std]:
        # 将有效比例凸度极限的最小值作为新的目标，之后进行重新计算ufd_pu_prf
        ef_ex_pu_prf = lim_df["ef_pu_prf_lim_min"][std]

        # 重新计算ufd_pu_prf
        ufd_pu_prf = lrg.calc(std, "UFD_PU_Prf3")(eppenv, ef_ex_pu_prf)

        # ufd状态异常，对>force_pu_wid_lim做偏移量为10的修正，在这里忽略
        # 从force_chg_clmp判定的条件分支开始
        istd_ex_pu_prf = lrg.calc(std, "Istd_Ex_PU_Prf0")(
            lim_df["std_ex_strn_lim_we"][std], ef_ex_pu_prf)
        ef_en_pu_prf = lrg.calc(std, "Ef_En_PU_Prf5")(
            lim_df["std_ex_strn_lim_we"][std], istd_ex_pu_prf)

        # 利用上一道次的ef_pu_prf_env来clamp获得ef_en_pu_prf_buf(注意是否要提前定义这个buf)
        ef_en_pu_prf_buf = mathuty.clamp(
            ef_en_pu_prf,
            env_df["ef_pu_prf_env_min"][std - 1],
            env_df["ef_pu_prf_env_max"][std - 1])

        # 更新move_prv标记
        move_prv_min = ((
            ef_en_pu_prf_buf !=
            env_df["ef_pu_prf_env_min"][std - 1]
        ) and (
            env_df["ef_pu_prf_env_min"][std - 1] !=
            env_df["ef_pu_prf_env_max"][std - 1]
        ))

        # 更新上一道次或入口有效单位凸度极限的最小值，注意是极限
        lim_df["ef_pu_prf_lim_min"][std - 1] = ef_en_pu_prf_buf

        # 如果不能前移，则将入口有效包络线的下限赋值给ef_en_pu_prf_buf
        if not move_prv_min:
            ef_en_pu_prf_buf = env_df["ef_pu_prf_env_min"][std - 1]

        # continue
