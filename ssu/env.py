# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

import lpce
import lrg
import crlc
import ufd
import global_setting as setting
import logging
logging.basicConfig(level=logging.INFO, filename="lrg_print.log")


std_vec = np.array([1, 2, 3, 4, 5, 67])


input_df = None
lpce_df = lpce.update()
lrg_df = lrg.update()

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
        lpce_df["bckl_lim_{}".format(bckl)])


# 计算各机架入口有效单位凸度极限范围
for std in std_vec:
    lim_df.loc[std - 1, "ef_pu_prf_lim_min"] = (
        lim_df.loc[std, "ufd_pu_prf_env_min"] -
        lim_df.loc[std, "std_ex_strn_lim_we"] *
        lrg_df.loc[std, "prf_chg_attn_fac"] / lrg_df.loc[std, "pce_infl_cof"])

    lim_df.loc[std - 1, "ef_pu_prf_lim_max"] = (
        lim_df.loc[std, "ufd_pu_prf_env_max"] -
        lim_df.loc[std, "std_ex_strn_lim_cb"] *
        lrg_df.loc[std, "prf_chg_attn_fac"] / lrg_df.loc[std, "pce_infl_cof"])
    if std == 7:
        lim_df.loc[std, "ef_pu_prf_lim_min"] = -1
        lim_df.loc[std, "ef_pu_prf_lim_max"] = 1
