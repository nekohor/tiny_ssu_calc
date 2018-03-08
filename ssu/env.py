# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from lpce import LateralPiece
from lrg import LateralRollGap
from ufd import UniForcDist
from crlc import CompositeRollStackCrown

import mathuty
import global_setting as setting
import logging
logging.basicConfig(level=logging.INFO, filename="env_print.log")


class Envelope():
    def __init__(self):
        self.pass_vec = np.array([0, 1, 2, 3, 4, 5, 6, 7])
        self.std_vec = np.array([1, 2, 3, 4, 5, 6, 7])


loop_count = 0
input_df = pd.read_excel(
    "{}M18001288W_input_sample.xlsx".format(setting.SAMPLE_DIR))

stk_cr_df = pd.read_excel(
    "{}M18001288W_stack_crown.xlsx".format(setting.SAMPLE_DIR))

ufd = UniForcDist(input_df)
lpce = LateralPiece(input_df)
lrg = LateralRollGap(input_df, lpce)
crlc = CompositeRollStackCrown(stk_cr_df)

# lim_nom dataframe
lim_df = pd.read_excel(
    "{}cfg_env/std_{}.xlsx".format(setting.CFG_DIR, setting.ROLL_LINE))
# logging.info(lim_df)

# 计算辊系凸度
lim_df["pce_wr_crn_lim_min"], lim_df["wr_br_crn_lim_min"] = (
    crlc.Crns_vector(lim_df["pos_shft_lim_min"]))

lim_df["pce_wr_crn_lim_max"], lim_df["wr_br_crn_lim_max"] = (
    crlc.Crns_vector(lim_df["pos_shft_lim_max"]))

# 计算单位轧制力
input_df["force_pu_wid"] = input_df["rolling_force"] / input_df["en_width"]
lim_df["force_pu_wid_lim_min"] = input_df["force_pu_wid"]
lim_df["force_pu_wid_lim_max"] = input_df["force_pu_wid"]

# nom窜辊位辊系凸度
lim_df["pce_wr_crn_nom"], lim_df["wr_br_crn_lim_nom"] = (
    crlc.Crns_vector(lim_df["pos_shft_nom"])
)

# lim的max/min与env中的min/max对应上
pass_vec = np.array([0, 1, 2, 3, 4, 5, 6, 7])
env_df = pd.DataFrame(index=pass_vec)
env_df["force_bnd_env_min"] = lim_df["force_bnd_lim_max"]
env_df["force_bnd_env_max"] = lim_df["force_bnd_lim_min"]

env_df["pos_shft_env_min"] = lim_df["pos_shft_lim_max"]
env_df["pos_shft_env_max"] = lim_df["pos_shft_lim_min"]

env_df["force_pu_wid_env_min"] = lim_df["force_pu_wid_lim_min"]
env_df["force_pu_wid_env_max"] = lim_df["force_pu_wid_lim_max"]

env_df["pce_wr_crn_env_min"] = lim_df["pce_wr_crn_lim_max"]
env_df["pce_wr_crn_env_max"] = lim_df["pce_wr_crn_lim_min"]

env_df["wr_br_crn_env_min"] = lim_df["wr_br_crn_lim_max"]
env_df["wr_br_crn_env_max"] = lim_df["wr_br_crn_lim_min"]
# logging.info(env_df)

std_vec = np.array([1, 2, 3, 4, 5, 6, 7])
for m__ in ["min", "max"]:
    for std in std_vec:
        env_df.loc[std, "ufd_pu_prf_env_{}".format(m__)] = (
            ufd.Prf(
                std,
                env_df["force_pu_wid_env_{}".format(m__)][std],
                env_df["force_bnd_env_{}".format(m__)][std],
                env_df["pce_wr_crn_env_{}".format(m__)][std],
                env_df["wr_br_crn_env_{}".format(m__)][std]) /
            input_df["ex_thick"][std])

bckl_list = ["we", "cb"]
for bckl in bckl_list:
    lim_df["std_ex_strn_lim_{}".format(bckl)] = (
        lpce.df["bckl_lim_{}".format(bckl)])


# 计算各机架入口有效单位凸度极限范围
# 后期用cLRGD::Ef_En_PU_Prf1(..)替换这个计算过程
for std in std_vec:
    lim_df.loc[std - 1, "ef_pu_prf_lim_min"] = (
        env_df.loc[std, "ufd_pu_prf_env_min"] -
        lim_df.loc[std, "std_ex_strn_lim_we"] *
        lrg.df.loc[std, "prf_chg_attn_fac"] / lrg.df.loc[std, "pce_infl_cof"])

    lim_df.loc[std - 1, "ef_pu_prf_lim_max"] = (
        env_df.loc[std, "ufd_pu_prf_env_max"] -
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
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # --------------- 计算各机架出口有效单位凸度包络线下限 -------------------
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    move_prv_min = False
    # 注意入口有效单位凸度包络线为上道次有效单位凸度包络线
    env_df.loc[std, "ef_pu_prf_env_min"] = lrg.calc(std, "Ef_Ex_PU_Prf3")(
        env_df["ef_pu_prf_env_min"][std - 1],
        env_df["ufd_pu_prf_env_min"][std])

    logging.info("ef_pu_prf_env_min")
    logging.info(env_df["ef_pu_prf_env_min"][std])
    logging.info("ef_pu_prf_lim_min")
    logging.info(lim_df["ef_pu_prf_lim_min"][std])
    logging.info(std)

    # 若出口有效单位凸度包络线下限小于极限值下限，修正出口有效单位凸度包络线下限
    if env_df["ef_pu_prf_env_min"][std] < lim_df["ef_pu_prf_lim_min"][std]:
        print("进行了修正")
        # 将有效比例凸度极限的最小值作为新的目标，之后进行重新计算ufd_pu_prf
        ef_ex_pu_prf = lim_df["ef_pu_prf_lim_min"][std]

        # 重新计算ufd_pu_prf
        # 注意入口有效单位凸度包络线为上道次有效单位凸度包络线
        ufd_pu_prf = lrg.calc(std, "UFD_PU_Prf3")(
            env_df["ef_pu_prf_env_min"][std - 1], ef_ex_pu_prf)

        # ufd状态异常，对>force_pu_wid_lim做偏移量为10的修正，在这里忽略
        # 从force_chg_clmp判定的条件分支开始
        istd_ex_pu_prf = lrg.calc(std, "Istd_Ex_PU_Prf0")(
            lim_df["std_ex_strn_lim_we"][std], ef_ex_pu_prf)
        ef_en_pu_prf = lrg.calc(std, "Ef_En_PU_Prf5")(
            lim_df["std_ex_strn_lim_we"][std], istd_ex_pu_prf)

        # 利用上一道次的ef_pu_prf_env来clamp获得ef_en_pu_prf_buf
        # (注意是否要提前定义这个buf)
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
        lim_df.loc[std - 1, "ef_pu_prf_lim_min"] = ef_en_pu_prf_buf

        # 如果不能前移，则将入口有效包络线的下限赋值给ef_en_pu_prf_buf
        if not move_prv_min:
            ef_en_pu_prf_buf = env_df["ef_pu_prf_env_min"][std - 1]

        # output (first) per unit prof
        pp_df = pd.DataFrame()
        pp_df.loc[std, "ef_en_pu_prf"] = ef_en_pu_prf
        pp_df.loc[std, "move_prv_min"] = move_prv_min

        # 输出后计算ufd单位凸度
        ufd_pu_prf = lrg.calc(std, "UFD_PU_Prf3")(
            ef_en_pu_prf_buf, ef_ex_pu_prf)

        # 之后是窜辊和弯辊力介入调整计算辊系凸度
        pce_wr_crn = lim_df["pce_wr_crn_nom"][std]
        wr_br_crn = lim_df["wr_br_crn_lim_nom"][std]
        pce_wr_crn, wr_br_crn = ufd.Crns(
            std,
            ufd_pu_prf * input_df["ex_thick"][std],
            env_df["force_pu_wid_env_min"][std],
            env_df["force_bnd_env_min"][std],
            pce_wr_crn,
            wr_br_crn)

        # 窜辊位置包络线下限更新
        env_df.loc[std, "pos_shft_env_min"] = crlc.Shft_Pos(
            std,
            pce_wr_crn,
            lim_df["pce_wr_crn_nom"],
            lim_df,
            env_df["pos_shft_env_min"][std])

        # 窜辊位置包络线下限限幅
        env_df.loc[std, "pos_shft_env_min"] = mathuty.clamp(
            env_df["pos_shft_env_min"][std],
            lim_df["pos_shft_lim_min"][std],
            lim_df["pos_shft_lim_max"][std])

        # 根据上面的窜辊位置重计算更新综合辊系凸度
        env_df["pce_wr_crn_env_min"], env_df["wr_br_crn_env_min"] = (
            crlc.Crns(std, env_df["pos_shft_env_min"][std])
        )

        # 用ufd.Pce_WR_Crn(..)计算pce_wr_crn
        pce_wr_crn = ufd.Pce_WR_Crn(
            std,
            ufd_pu_prf * input_df["ex_thick"][std],
            env_df["force_pu_wid_env_min"][std],
            env_df["force_bnd_env_min"][std],
            env_df["wr_br_crn_env_min"][std])

        # 更新弯辊力包络线的下限
        force_bnd_des = ufd.Bnd_Frc(
            std,
            ufd_pu_prf * input_df["ex_thick"][std],
            env_df["force_pu_wid_env_min"][std],
            env_df["pce_wr_crn_env_min"][std],
            env_df["wr_br_crn_env_min"][std])

        # 弯辊力计算值和原值是否相等的指示器
        force_bnd_clmp = (force_bnd_des != env_df["force_bnd_env_min"][std])

        # 计算均载辊缝单位凸度包络线下限
        env_df["ufd_pu_prf_env_min"][std] = ufd.Prf(
            std,
            env_df["force_pu_wid_env_min"][std],
            env_df["force_bnd_env_min"][std],
            env_df["pce_wr_crn_env_min"][std],
            env_df["wr_br_crn_env_min"][std]) / input_df["ex_thick"][std]

        # force_bnd_clmp判断以及处理有效单位凸度
        if force_bnd_clmp:
            force_bnd_clmp = False
            ef_en_pu_prf = lrg.calc(std, "Ef_En_PU_Prf3")(
                env_df["ufd_pu_prf_env_min"][std], ef_ex_pu_prf)

            # 对入口有效单位凸度进行限幅
            ef_en_pu_prf_buf = mathuty.clamp(
                ef_en_pu_prf,
                env_df["ef_pu_prf_env_min"][std - 1],
                env_df["ef_pu_prf_env_max"][std - 1])
            # move_prv指示器更新
            move_prv_min = move_prv_min | ((
                ef_en_pu_prf_buf !=
                env_df["ef_pu_prf_env_min"][std - 1]) & (
                env_df["ef_pu_prf_env_min"][std - 1] !=
                env_df["ef_pu_prf_env_max"][std - 1]))
            lim_df["ef_pu_prf_lim_min"][std - 1] = ef_en_pu_prf_buf

    # ----------------------------------------------------
    # ----------------- 浪形失稳条件判断 -----------------
    # ----------------------------------------------------
    if not move_prv_min:
        std_ex_strn = lrg.calc(std, "Std_Ex_Strn1")(
            env_df["ef_pu_prf_env_min"][std - 1],
            env_df["ufd_pu_prf_env_min"][std])
        # std_ex_strn低于出口应变差中浪极限

        # std_ex_strn高于出口应变差边浪极限

    # ++++++++++++++++ 最终计算有效单位凸度下限 +++++++++++++++++++
    env_df["ef_pu_prf_env_min"][std] = lrg.calc(std, "Ef_Ex_PU_Prf3")(
        env_df["ef_pu_prf_env_min"][std - 1],
        env_df["ufd_pu_prf_env_min"][std])

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # --------------- 计算各机架出口有效单位凸度包络线上限 -------------------
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # 注意入口有效单位凸度包络线为上道次有效单位凸度包络线
    move_prv_max = False
    # 注意入口有效单位凸度包络线为上道次有效单位凸度包络线
    env_df.loc[std, "ef_pu_prf_env_max"] = lrg.calc(std, "Ef_Ex_PU_Prf3")(
        env_df["ef_pu_prf_env_max"][std - 1],
        env_df["ufd_pu_prf_env_max"][std])

    # 若出口有效单位凸度包络线上限小于极限值上限，修正出口有效单位凸度包络线上限
    if env_df["ef_pu_prf_env_max"][std] > lim_df["ef_pu_prf_lim_max"][std]:
        # 将有效比例凸度极限的最小值作为新的目标，之后进行重新计算ufd_pu_prf
        ef_ex_pu_prf = lim_df["ef_pu_prf_lim_max"][std]

        # 重新计算ufd_pu_prf
        # 注意入口有效单位凸度包络线为上道次有效单位凸度包络线
        ufd_pu_prf = lrg.calc(std, "UFD_PU_Prf3")(
            env_df["ef_pu_prf_env_max"][std - 1], ef_ex_pu_prf)

        # ufd状态异常，对>force_pu_wid_lim做偏移量为10的修正，在这里忽略
        # 从force_chg_clmp判定的条件分支开始
        istd_ex_pu_prf = lrg.calc(std, "Istd_Ex_PU_Prf0")(
            lim_df["std_ex_strn_lim_we"][std], ef_ex_pu_prf)
        ef_en_pu_prf = lrg.calc(std, "Ef_En_PU_Prf5")(
            lim_df["std_ex_strn_lim_we"][std], istd_ex_pu_prf)

        # 利用上一道次的ef_pu_prf_env来clamp获得ef_en_pu_prf_buf
        # (注意是否要提前定义这个buf)
        ef_en_pu_prf_buf = mathuty.clamp(
            ef_en_pu_prf,
            env_df["ef_pu_prf_env_max"][std - 1],
            env_df["ef_pu_prf_env_max"][std - 1])

        # 更新move_prv标记
        move_prv_max = ((
            ef_en_pu_prf_buf !=
            env_df["ef_pu_prf_env_max"][std - 1]
        ) and (
            env_df["ef_pu_prf_env_max"][std - 1] !=
            env_df["ef_pu_prf_env_max"][std - 1]
        ))

        # 更新上一道次或入口有效单位凸度极限的最小值，注意是极限
        lim_df.loc[std - 1, "ef_pu_prf_lim_max"] = ef_en_pu_prf_buf

        # 如果不能前移，则将入口有效包络线的上限赋值给ef_en_pu_prf_buf
        if not move_prv_max:
            ef_en_pu_prf_buf = env_df["ef_pu_prf_env_max"][std - 1]

        # output (first) per unit prof
        pp_df = pd.DataFrame()
        pp_df.loc[std, "ef_en_pu_prf"] = ef_en_pu_prf
        pp_df.loc[std, "move_prv_max"] = move_prv_max

        # 输出后计算ufd单位凸度
        ufd_pu_prf = lrg.calc(std, "UFD_PU_Prf3")(
            ef_en_pu_prf_buf, ef_ex_pu_prf)

        # 之后是窜辊和弯辊力介入调整计算辊系凸度
        pce_wr_crn = lim_df["pce_wr_crn_nom"][std]
        wr_br_crn = lim_df["wr_br_crn_lim_nom"][std]
        pce_wr_crn, wr_br_crn = ufd.Crns(
            std,
            ufd_pu_prf * input_df["ex_thick"][std],
            env_df["force_pu_wid_env_max"][std],
            env_df["force_bnd_env_max"][std],
            pce_wr_crn,
            wr_br_crn)

        # 窜辊位置包络线上限更新
        env_df.loc[std, "pos_shft_env_max"] = crlc.Shft_Pos(
            std,
            pce_wr_crn,
            lim_df["pce_wr_crn_nom"],
            lim_df,
            env_df["pos_shft_env_max"][std])

        # 窜辊位置包络线上限限幅
        env_df.loc[std, "pos_shft_env_max"] = mathuty.clamp(
            env_df["pos_shft_env_max"][std],
            lim_df["pos_shft_lim_max"][std],
            lim_df["pos_shft_lim_max"][std])

        # 根据上面的窜辊位置重计算更新综合辊系凸度
        env_df["pce_wr_crn_env_max"], env_df["wr_br_crn_env_max"] = (
            crlc.Crns(std, env_df["pos_shft_env_max"][std])
        )

        # 用ufd.Pce_WR_Crn(..)计算pce_wr_crn
        pce_wr_crn = ufd.Pce_WR_Crn(
            std,
            ufd_pu_prf * input_df["ex_thick"][std],
            env_df["force_pu_wid_env_max"][std],
            env_df["force_bnd_env_max"][std],
            env_df["wr_br_crn_env_max"][std])

        # 更新弯辊力包络线的上限
        force_bnd_des = ufd.Bnd_Frc(
            std,
            ufd_pu_prf * input_df["ex_thick"][std],
            env_df["force_pu_wid_env_max"][std],
            env_df["pce_wr_crn_env_max"][std],
            env_df["wr_br_crn_env_max"][std])

        # 弯辊力计算值和原值是否相等的指示器
        force_bnd_clmp = (force_bnd_des != env_df["force_bnd_env_max"][std])

        # 计算均载辊缝单位凸度包络线上限
        env_df["ufd_pu_prf_env_max"][std] = ufd.Prf(
            std,
            env_df["force_pu_wid_env_max"][std],
            env_df["force_bnd_env_max"][std],
            env_df["pce_wr_crn_env_max"][std],
            env_df["wr_br_crn_env_max"][std]) / input_df["ex_thick"][std]

        # force_bnd_clmp判断以及处理有效单位凸度
        if force_bnd_clmp:
            force_bnd_clmp = False
            ef_en_pu_prf = lrg.calc(std, "Ef_En_PU_Prf3")(
                env_df["ufd_pu_prf_env_max"][std], ef_ex_pu_prf)

            # 对入口有效单位凸度进行限幅
            ef_en_pu_prf_buf = mathuty.clamp(
                ef_en_pu_prf,
                env_df["ef_pu_prf_env_max"][std - 1],
                env_df["ef_pu_prf_env_max"][std - 1])
            # move_prv指示器更新
            move_prv_max = move_prv_max | ((
                ef_en_pu_prf_buf !=
                env_df["ef_pu_prf_env_max"][std - 1]
            ) & (
                env_df["ef_pu_prf_env_max"][std - 1] !=
                env_df["ef_pu_prf_env_max"][std - 1]
            ))
            lim_df["ef_pu_prf_lim_max"][std - 1] = ef_en_pu_prf_buf

    # ----------------------------------------------------
    # ----------------- 浪形失稳条件判断 -----------------
    # ----------------------------------------------------
    if not move_prv_max:
        std_ex_strn = lrg.calc(std, "Std_Ex_Strn1")(
            env_df["ef_pu_prf_env_max"][std - 1],
            env_df["ufd_pu_prf_env_max"][std])
        # std_ex_strn低于出口应变差中浪极限

        # std_ex_strn高于出口应变差边浪极限

    # ++++++++++++++++ 最终计算有效单位凸度上限 +++++++++++++++++++
    env_df["ef_pu_prf_env_max"][std] = lrg.calc(std, "Ef_Ex_PU_Prf3")(
        env_df["ef_pu_prf_env_max"][std - 1],
        env_df["ufd_pu_prf_env_max"][std])

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # ------------------------ 每个循环周期末的迭代处理 ----------------------
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if move_prv_min | move_prv_max:
        loop_count = loop_count + 1
        if loop_count > pow(pass_vec[-1] - 1, 2):
            if 7 == std:
                break
            else:
                std = std + 1
        else:
            std = std - 1
    else:
        if 7 == std:
            break
        else:
            std = std + 1
    # 结束--计算各机架出口有效单位凸度包络线下限和上限，在循环中进行

# loop_count计数器 超出极限的监控
if loop_count > pow(pass_vec[-1] - 2, 2):
    logging.info("loop counter exceeded limit")

# =============== 最后一波计算以及检查确认工作 ===================
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

        env_df.loc[std, "ef_pu_prf_env_{}".format(m__)] = (
            lrg.calc(std, "Ef_Ex_PU_Prf3")(
                env_df["ef_pu_prf_env_{}".format(m__)][std - 1],
                env_df["ufd_pu_prf_env_{}".format(m__)][std]))

        std_ex_strn = lrg.calc(std, "Std_Ex_Strn1")(
            env_df["ef_pu_prf_env_{}".format(m__)][std],
            env_df["ufd_pu_prf_env_{}".format(m__)][std])

        # 计算比例凸度包络线上下限
        env_df.loc[std, "pu_prf_env_{}".format(m__)] = (
            lrg.calc(std, "Istd_Ex_PU_Prf0")(
                std_ex_strn,
                env_df["ef_pu_prf_env_{}".format(m__)][std]))

    # 检查确认
    parameter_list = [
        "pu_prf_env",
        "ef_pu_prf_env",
        "ufd_pu_prf_env",
        "force_pu_wid_env"]

    for para in parameter_list:
        scratch = max(
            env_df["{}_min".format(para)][std],
            env_df["{}_max".format(para)][std])

        env_df["{}_min".format(para)][std] = min(
            env_df["{}_min".format(para)][std],
            env_df["{}_max".format(para)][std])

        env_df["{}_max".format(para)][std] = scratch

    # 迭代计数器处理
    if 7 == std:
        break
    else:
        std = std + 1


print(env_df)
print(loop_count)
