# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from lpce import LateralPiece
from lrg import LateralRollGap
from ufd import UniForcDist
from crlc import CompositeRollStackCrown

from utils import mathuty
import logging
logging.basicConfig(level=logging.INFO, filename="env_print.log")


class ProfileEnvelope():
    def __init__(self, fsstd, lpce, lrg, ufd, crlc):
        self.pass_vec = np.array([0, 1, 2, 3, 4, 5, 6, 7])
        self.std_vec = np.array([1, 2, 3, 4, 5, 6, 7])
        self.fsstd = fsstd

        self.lpce = lpce
        self.lrg = lrg
        self.ufd = ufd
        self.crlc = crlc

        self.d = pd.DataFrame()
        self.func = pd.DataFrame()

    def Calculate(self):
        # logging.info(self.fsstd.lim)

        # lim的max/min与env中的min/max对应上
        self.d = pd.DataFrame(index=self.pass_vec)
        self.d["force_bnd_env_min"] = self.fsstd.lim["force_bnd_lim_max"]
        self.d["force_bnd_env_max"] = self.fsstd.lim["force_bnd_lim_min"]

        self.d["pos_shft_env_min"] = self.fsstd.lim["wr_shft_lim_max"]
        self.d["pos_shft_env_max"] = self.fsstd.lim["wr_shft_lim_min"]

        for std in self.std_vec:
            tmp = self.crlc.Crns(std, self.fsstd.lim["wr_shft_lim_min"][std])
            self.d.loc[std, "pce_wr_crn_lim_min"] = tmp[0]
            self.d.loc[std, "wr_br_crn_lim_min"] = tmp[1]

            tmp = self.crlc.Crns(std, self.fsstd.lim["wr_shft_lim_max"][std])
            self.d.loc[std, "pce_wr_crn_lim_max"] = tmp[0]
            self.d.loc[std, "wr_br_crn_lim_max"] = tmp[1]

        # 678-679 line
        self.d["force_pu_wid"] = (self.fsstd.d["force_strip"] /
                                  self.fsstd.d["en_width"])
        self.d["force_pu_wid_lim_min"] = self.d["force_pu_wid"]
        self.d["force_pu_wid_lim_max"] = self.d["force_pu_wid"]

        for std in self.std_vec:
            # 此时的pce_wr_crn和wr_br_crn是用wr_shft_nom求得的
            self.d.loc[std, "pce_wr_crn"], self.d.loc[std, "wr_br_crn"] = (
                self.crlc.Crns(std, self.fsstd.lim["wr_shft_nom"][std])
            )

        for std in self.std_vec:
            self.func.loc[std, "dprf_dfrcw"] = self.ufd.Dprf_Dfrcw(
                std,
                self.d["force_pu_wid"][std],
                self.fsstd.lim["force_bnd_nom"][std],
                self.d["pce_wr_crn"][std],  # 此时仍然对应nom
                self.d["wr_br_crn"][std]    # 此时仍然对应nom
            )
            if self.func.loc[std, "dprf_dfrcw"] >= 0:
                self.d.loc[std, "force_pu_wid_env_min"] = (
                    self.d.loc[std, "force_pu_wid_lim_min"])
                self.d.loc[std, "force_pu_wid_env_max"] = (
                    self.d.loc[std, "force_pu_wid_lim_max"])
            else:
                self.d.loc[std, "force_pu_wid_env_min"] = (
                    self.d.loc[std, "force_pu_wid_lim_max"])
                self.d.loc[std, "force_pu_wid_env_max"] = (
                    self.d.loc[std, "force_pu_wid_lim_min"])

        self.d["pce_wr_crn_env_min"] = self.d["pce_wr_crn_lim_max"]
        self.d["wr_br_crn_env_min"] = self.d["wr_br_crn_lim_max"]
        self.d["pce_wr_crn_env_max"] = self.d["pce_wr_crn_lim_min"]
        self.d["wr_br_crn_env_max"] = self.d["wr_br_crn_lim_min"]

        # logging.info(self.d)

        for m in ["min", "max"]:
            for std in self.std_vec:
                self.d.loc[std, "ufd_pu_prf_env_{}".format(m)] = (
                    self.ufd.Prf(
                        std,
                        self.d["force_pu_wid_env_{}".format(m)][std],
                        self.d["force_bnd_env_{}".format(m)][std],
                        self.d["pce_wr_crn_env_{}".format(m)][std],
                        self.d["wr_br_crn_env_{}".format(m)][std]) /
                    self.fsstd.d["ex_thick"][std])
        # 至此前段非空过部分结束

        bckl_list = ["we", "cb"]
        for bckl in bckl_list:
            self.d["std_ex_strn_lim_{}".format(bckl)] = (
                self.lpce.d["crit_bckl_lim_{}".format(bckl)])

        # 计算各机架入口有效单位凸度极限范围
        # 忽略带钢影响系数小于0的情况（pce_infl_cof<pce_infl_cof_mn）直接计算
        # 后期用cLRGD::Ef_En_PU_Prf1(..)替换这个计算过程
        for std in self.std_vec:
            self.d.loc[std - 1, "ef_pu_prf_lim_min"] = self.lrg.calc(
                std, "Ef_En_PU_Prf1")(
                self.d.loc[std, "ufd_pu_prf_env_min"],
                self.d.loc[std, "std_ex_strn_lim_we"])

            self.d.loc[std - 1, "ef_pu_prf_lim_max"] = self.lrg.calc(
                std, "Ef_En_PU_Prf1")(
                self.d.loc[std, "ufd_pu_prf_env_max"],
                self.d.loc[std, "std_ex_strn_lim_cb"])

        self.d.loc[7, "ef_pu_prf_lim_min"] = -1
        self.d.loc[7, "ef_pu_prf_lim_max"] = 1

        # mean指的意思是都一样的, 初始化中间坯的ef_pu_prf_env为
        self.d.loc[0, "ef_pu_prf_env_min"] = self.fsstd.d["pu_prf_pass0"][1]
        self.d.loc[0, "ef_pu_prf_env_max"] = self.fsstd.d["pu_prf_pass0"][1]

        # 包络线对应的极限机架号
        # pas_env_lim_min = 0
        # pas_env_lim_max = 0

        # ========================= 协调单位凸度包络线 ================================
        loop_count = 0
        std = 1
        while (std >= 1) & (std <= 7):
            print("协调机架", std)
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # --------------- 计算各机架出口有效单位凸度包络线下限 -------------------
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            move_prv_min = False
            # 注意入口有效单位凸度包络线为上道次有效单位凸度包络线
            self.d.loc[std, "ef_pu_prf_env_min"] = self.lrg.calc(
                std, "Ef_Ex_PU_Prf3")(
                self.d["ef_pu_prf_env_min"][std - 1],
                self.d["ufd_pu_prf_env_min"][std])

            # print(self.d.loc[std, "ef_pu_prf_env_min"])
            # print(self.d.loc[std, "ef_pu_prf_lim_max"])

            # 若出口有效单位凸度包络线下限小于极限值下限，修正出口有效单位凸度包络线下限
            if (self.d["ef_pu_prf_env_min"][std] <
                    self.d["ef_pu_prf_lim_min"][std]):
                print("进行了修正min")

                # pas_env_lim的mathuty.max处理

                # 将有效比例凸度极限的最小值作为新的目标，之后进行重新计算ufd_pu_prf
                ef_ex_pu_prf = self.d["ef_pu_prf_lim_min"][std]

                # 重新计算ufd_pu_prf
                # 注意入口有效单位凸度包络线为上道次有效单位凸度包络线
                ufd_pu_prf = self.lrg.calc(std, "UFD_PU_Prf3")(
                    self.d["ef_pu_prf_env_min"][std - 1], ef_ex_pu_prf)

                # ufd状态异常，对>force_pu_wid_lim做偏移量为10的修正，在这里忽略

                # 从force_chg_clmp判定的条件分支开始
                istd_ex_pu_prf = self.lrg.calc(std, "Istd_Ex_PU_Prf0")(
                    self.d["std_ex_strn_lim_we"][std], ef_ex_pu_prf)
                ef_en_pu_prf = self.lrg.calc(std, "Ef_En_PU_Prf5")(
                    self.d["std_ex_strn_lim_we"][std], istd_ex_pu_prf)

                # 利用上一道次的ef_pu_prf_env来Clamp获得ef_en_pu_prf_buf
                # (注意是否要提前定义这个ef_en_pu_prf_buf)
                ef_en_pu_prf_buf = mathuty.Clamp(
                    ef_en_pu_prf,
                    self.d["ef_pu_prf_env_min"][std - 1],
                    self.d["ef_pu_prf_env_max"][std - 1])

                # 更新move_prv标记
                move_prv_min = ((
                    ef_en_pu_prf_buf !=
                    self.d["ef_pu_prf_env_min"][std - 1]
                ) & (
                    self.d["ef_pu_prf_env_min"][std - 1] !=
                    self.d["ef_pu_prf_env_max"][std - 1]
                ))

                # 更新上一道次或入口有效单位凸度极限的最小值，注意是极限
                self.d.loc[std - 1, "ef_pu_prf_lim_min"] = ef_en_pu_prf_buf

                # 如果不能前移，则将入口有效包络线的下限赋值给ef_en_pu_prf_buf
                if not move_prv_min:
                    ef_en_pu_prf_buf = self.d["ef_pu_prf_env_min"][std - 1]
                # --- force_chg_clmp判定的条件分支结束 ---

                # 输出后计算ufd单位凸度
                ufd_pu_prf = self.lrg.calc(std, "UFD_PU_Prf3")(
                    ef_en_pu_prf_buf, ef_ex_pu_prf)

                # 之后是窜辊和弯辊力介入调整计算辊系凸度
                # 注意pce_wr_crn和wr_br_crn为两个变化中的状态量
                tmp = self.ufd.Crns(
                    std,
                    ufd_pu_prf * self.fsstd.d["ex_thick"][std],
                    self.d["force_pu_wid_env_min"][std],
                    self.d["force_bnd_env_min"][std],
                    self.d["pce_wr_crn"][std],
                    self.d["wr_br_crn"][std])
                self.d.loc[std, "pce_wr_crn"] = tmp[0]
                self.d.loc[std, "wr_br_crn"] = tmp[1]

                # 窜辊位置包络线下限更新
                self.d.loc[std, "pos_shft_env_min"] = self.crlc.Shft_Pos(
                    std,
                    self.d["pce_wr_crn"][std],
                    self.fsstd.lim["wr_shft_lim_min"][std],
                    self.fsstd.lim["wr_shft_lim_max"][std],
                    self.d["pos_shft_env_min"][std])

                # 根据上面的窜辊位置重计算更新综合辊系凸度
                tmp = self.crlc.Crns(std, self.d["pos_shft_env_min"][std])
                self.d.loc[std, "pce_wr_crn_env_min"] = tmp[0]
                self.d.loc[std, "wr_br_crn_env_min"] = tmp[1]

                # 用ufd.Pce_WR_Crn(..)计算pce_wr_crn
                self.d.loc[std, "pce_wr_crn"] = self.ufd.Pce_WR_Crn(
                    std,
                    ufd_pu_prf * self.fsstd.d["ex_thick"][std],
                    self.d["force_pu_wid_env_min"][std],
                    self.d["force_bnd_env_min"][std],
                    self.d["wr_br_crn_env_min"][std]
                )

                # Re-calculate the following composite roll stack crown
                # 再次更新计算pce_wr_crn和wr_br_crn之后才能更新计算弯辊力下限
                tmp = self.crlc.Crns(std, self.d["pos_shft_env_min"][std])
                self.d.loc[std, "pce_wr_crn_env_min"] = tmp[0]
                self.d.loc[std, "wr_br_crn_env_min"] = tmp[1]

                # 更新弯辊力包络线的下限
                tmp = self.ufd.Bnd_Frc(
                    std,
                    ufd_pu_prf * self.fsstd.d["ex_thick"][std],
                    self.d["force_pu_wid_env_min"][std],
                    self.d["pce_wr_crn_env_min"][std],
                    self.d["wr_br_crn_env_min"][std],
                    self.fsstd.lim["force_bnd_lim_min"][std],
                    self.fsstd.lim["force_bnd_lim_max"][std])
                self.d.loc[std, "force_bnd_env_min"] = tmp[0]
                force_bnd_des = tmp[1]

                # 弯辊力计算值和原值是否相等的指示器
                force_bnd_clmp = (
                    force_bnd_des != self.d["force_bnd_env_min"][std])

                # 计算均载辊缝单位凸度包络线下限
                self.d.loc[std, "ufd_pu_prf_env_min"] = (
                    self.ufd.Prf(
                        std,
                        self.d["force_pu_wid_env_min"][std],
                        self.d["force_bnd_env_min"][std],
                        self.d["pce_wr_crn_env_min"][std],
                        self.d["wr_br_crn_env_min"][std]) /
                    self.fsstd.d["ex_thick"][std])

                # force_bnd_clmp判断以及处理有效单位凸度,忽略了带钢影响系数的判断
                if force_bnd_clmp:
                    force_bnd_clmp = False
                    ef_en_pu_prf = self.lrg.calc(std, "Ef_En_PU_Prf3")(
                        self.d["ufd_pu_prf_env_min"][std], ef_ex_pu_prf)

                    # 对入口有效单位凸度进行限幅
                    ef_en_pu_prf_buf = mathuty.Clamp(
                        ef_en_pu_prf,
                        self.d["ef_pu_prf_env_min"][std - 1],
                        self.d["ef_pu_prf_env_max"][std - 1])
                    # move_prv指示器更新
                    move_prv_min = move_prv_min | ((
                        ef_en_pu_prf_buf !=
                        self.d["ef_pu_prf_lim_min"][std - 1]) & (
                        self.d["ef_pu_prf_env_min"][std - 1] !=
                        self.d["ef_pu_prf_env_max"][std - 1]))

                    self.d.loc[std - 1, "ef_pu_prf_lim_min"] = ef_en_pu_prf_buf

            # ----------------------------------------------------
            # ----------------- 浪形失稳条件判断 -----------------
            # ----------------------------------------------------
            if not move_prv_min:
                std_ex_strn = self.lrg.calc(std, "Std_Ex_Strn1")(
                    self.d["ef_pu_prf_env_min"][std - 1],
                    self.d["ufd_pu_prf_env_min"][std])
                # std_ex_strn低于出口应变差中浪极限
                # 被 1 < 0 掐掉

                # std_ex_strn高于出口应变差边浪极限
                # 被 1 < 0 掐掉

            # ++++++++++++++++ 最终计算有效单位凸度下限(算是更新) +++++++++++++++++++
            self.d.loc[std, "ef_pu_prf_env_min"] = self.lrg.calc(
                std, "Ef_Ex_PU_Prf3")(
                self.d["ef_pu_prf_env_min"][std - 1],
                self.d["ufd_pu_prf_env_min"][std])

            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # --------------- 计算各机架出口有效单位凸度包络线上限 -------------------
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # 注意入口有效单位凸度包络线为上道次有效单位凸度包络线
            move_prv_max = False
            # 注意入口有效单位凸度包络线为上道次有效单位凸度包络线
            self.d.loc[std, "ef_pu_prf_env_max"] = self.lrg.calc(
                std, "Ef_Ex_PU_Prf3")(
                self.d["ef_pu_prf_env_max"][std - 1],
                self.d["ufd_pu_prf_env_max"][std])

            # print(self.d.loc[std, "ef_pu_prf_env_max"])
            # print(self.d.loc[std, "ef_pu_prf_lim_max"])

            # 若出口有效单位凸度包络线下限小于极限值下限，修正出口有效单位凸度包络线下限
            if (self.d["ef_pu_prf_env_max"][std] >
                    self.d["ef_pu_prf_lim_max"][std]):
                print("进行了修正max")

                # pas_env_lim的mathuty.max处理

                # 将有效比例凸度极限的最小值作为新的目标，之后进行重新计算ufd_pu_prf
                ef_ex_pu_prf = self.d["ef_pu_prf_lim_max"][std]

                # 重新计算ufd_pu_prf
                # 注意入口有效单位凸度包络线为上道次有效单位凸度包络线
                ufd_pu_prf = self.lrg.calc(std, "UFD_PU_Prf3")(
                    self.d["ef_pu_prf_env_max"][std - 1], ef_ex_pu_prf)

                # ufd状态异常，对>force_pu_wid_lim做偏移量为10的修正，在这里忽略

                # 从force_chg_clmp判定的条件分支开始
                istd_ex_pu_prf = self.lrg.calc(std, "Istd_Ex_PU_Prf0")(
                    self.d["std_ex_strn_lim_cb"][std], ef_ex_pu_prf)
                ef_en_pu_prf = self.lrg.calc(std, "Ef_En_PU_Prf5")(
                    self.d["std_ex_strn_lim_cb"][std], istd_ex_pu_prf)

                # 利用上一道次的ef_pu_prf_env来Clamp获得ef_en_pu_prf_buf
                # (注意是否要提前定义这个ef_en_pu_prf_buf)
                ef_en_pu_prf_buf = mathuty.Clamp(
                    ef_en_pu_prf,
                    self.d["ef_pu_prf_env_max"][std - 1],
                    self.d["ef_pu_prf_env_max"][std - 1])

                # 更新move_prv标记
                move_prv_max = ((
                    ef_en_pu_prf_buf !=
                    self.d["ef_pu_prf_env_max"][std - 1]
                ) & (
                    self.d["ef_pu_prf_env_max"][std - 1] !=
                    self.d["ef_pu_prf_env_max"][std - 1]
                ))

                # 更新上一道次或入口有效单位凸度极限的最小值，注意是极限
                self.d.loc[std - 1, "ef_pu_prf_lim_max"] = ef_en_pu_prf_buf

                # 如果不能前移，则将入口有效包络线的下限赋值给ef_en_pu_prf_buf
                if not move_prv_max:
                    ef_en_pu_prf_buf = self.d["ef_pu_prf_env_max"][std - 1]
                # --- force_chg_clmp判定的条件分支结束 ---

                # 输出后计算ufd单位凸度
                ufd_pu_prf = self.lrg.calc(std, "UFD_PU_Prf3")(
                    ef_en_pu_prf_buf, ef_ex_pu_prf)

                # 之后是窜辊和弯辊力介入调整计算辊系凸度
                # 注意pce_wr_crn和wr_br_crn为两个变化中的状态量
                tmp = self.ufd.Crns(
                    std,
                    ufd_pu_prf * self.fsstd.d["ex_thick"][std],
                    self.d["force_pu_wid_env_max"][std],
                    self.d["force_bnd_env_max"][std],
                    self.d["pce_wr_crn"][std],
                    self.d["wr_br_crn"][std])
                self.d.loc[std, "pce_wr_crn"] = tmp[0]
                self.d.loc[std, "wr_br_crn"] = tmp[1]

                # 窜辊位置包络线下限更新
                self.d.loc[std, "pos_shft_env_max"] = self.crlc.Shft_Pos(
                    std,
                    self.d["pce_wr_crn"][std],
                    self.fsstd.lim["wr_shft_lim_min"][std],
                    self.fsstd.lim["wr_shft_lim_max"][std],
                    self.d["pos_shft_env_max"][std])

                # 根据上面的窜辊位置重计算更新综合辊系凸度
                tmp = self.crlc.Crns(std, self.d["pos_shft_env_max"][std])
                self.d.loc[std, "pce_wr_crn_env_max"] = tmp[0]
                self.d.loc[std, "wr_br_crn_env_max"] = tmp[1]

                # 用ufd.Pce_WR_Crn(..)计算pce_wr_crn
                self.d.loc[std, "pce_wr_crn"] = self.ufd.Pce_WR_Crn(
                    std,
                    ufd_pu_prf * self.fsstd.d["ex_thick"][std],
                    self.d["force_pu_wid_env_max"][std],
                    self.d["force_bnd_env_max"][std],
                    self.d["wr_br_crn_env_max"][std]
                )

                # Re-calculate the following composite roll stack crown
                # 再次更新计算pce_wr_crn和wr_br_crn之后才能更新计算弯辊力下限
                tmp = self.crlc.Crns(std, self.d["pos_shft_env_max"][std])
                self.d.loc[std, "pce_wr_crn_env_max"] = tmp[0]
                self.d.loc[std, "wr_br_crn_env_max"] = tmp[1]

                # 更新弯辊力包络线的下限
                tmp = self.ufd.Bnd_Frc(
                    std,
                    ufd_pu_prf * self.fsstd.d["ex_thick"][std],
                    self.d["force_pu_wid_env_max"][std],
                    self.d["pce_wr_crn_env_max"][std],
                    self.d["wr_br_crn_env_max"][std],
                    self.fsstd.lim["force_bnd_lim_min"][std],
                    self.fsstd.lim["force_bnd_lim_max"][std])
                self.d.loc[std, "force_bnd_env_max"] = tmp[0]
                force_bnd_des = tmp[1]

                # 弯辊力计算值和原值是否相等的指示器
                force_bnd_clmp = (
                    force_bnd_des != self.d["force_bnd_env_max"][std])

                # 计算均载辊缝单位凸度包络线下限
                self.d.loc[std, "ufd_pu_prf_env_max"] = (
                    self.ufd.Prf(
                        std,
                        self.d["force_pu_wid_env_max"][std],
                        self.d["force_bnd_env_max"][std],
                        self.d["pce_wr_crn_env_max"][std],
                        self.d["wr_br_crn_env_max"][std]) /
                    self.fsstd.d["ex_thick"][std])

                # force_bnd_clmp判断以及处理有效单位凸度,忽略了带钢影响系数的判断
                if force_bnd_clmp:
                    force_bnd_clmp = False
                    ef_en_pu_prf = self.lrg.calc(std, "Ef_En_PU_Prf3")(
                        self.d["ufd_pu_prf_env_max"][std], ef_ex_pu_prf, ef_en_pu_prf)

                    # 对入口有效单位凸度进行限幅
                    ef_en_pu_prf_buf = mathuty.Clamp(
                        ef_en_pu_prf,
                        self.d["ef_pu_prf_env_max"][std - 1],
                        self.d["ef_pu_prf_env_max"][std - 1])
                    # move_prv指示器更新
                    move_prv_max = move_prv_max | ((
                        ef_en_pu_prf_buf !=
                        self.d["ef_pu_prf_lim_max"][std - 1]) & (
                        self.d["ef_pu_prf_env_max"][std - 1] !=
                        self.d["ef_pu_prf_env_max"][std - 1]))

                    self.d.loc[std - 1, "ef_pu_prf_lim_max"] = ef_en_pu_prf_buf

            # ----------------------------------------------------
            # ----------------- 浪形失稳条件判断 -----------------
            # ----------------------------------------------------
            if not move_prv_max:
                std_ex_strn = self.lrg.calc(std, "Std_Ex_Strn1")(
                    self.d["ef_pu_prf_env_max"][std - 1],
                    self.d["ufd_pu_prf_env_max"][std])
                # std_ex_strn低于出口应变差中浪极限
                # 被 1 < 0 掐掉

                # std_ex_strn高于出口应变差边浪极限
                # 被 1 < 0 掐掉

            # ++++++++++++++++ 最终计算有效单位凸度下限(算是更新) +++++++++++++++++++
            self.d.loc[std, "ef_pu_prf_env_max"] = self.lrg.calc(
                std, "Ef_Ex_PU_Prf3")(
                self.d["ef_pu_prf_env_max"][std - 1],
                self.d["ufd_pu_prf_env_max"][std])

            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # ------------------------ 每个循环周期末的迭代处理 ----------------------
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            if move_prv_min | move_prv_max:
                loop_count = loop_count + 1
                if loop_count > pow(self.pass_vec[-1] - 1, 2):
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
        if loop_count > pow(self.pass_vec[-1] - 2, 2):
            print("loop counter exceeded limit")
            logging.info("loop counter exceeded limit")

        # =============== 最后一波计算以及检查确认工作 ===================
        std = 1
        while std > 0:
            mxx_list = ["max", "min"]
            for m__ in mxx_list:
                self.d.loc[std, "ufd_pu_prf_env_{}".format(m__)] = (
                    self.ufd.Prf(
                        std,
                        self.d["force_pu_wid_env_{}".format(m__)][std],
                        self.d["force_bnd_env_{}".format(m__)][std],
                        self.d["pce_wr_crn_env_{}".format(m__)][std],
                        self.d["wr_br_crn_env_{}".format(m__)][std]) /
                    self.fsstd.d["ex_thick"][std])

                self.d.loc[std, "ef_pu_prf_env_{}".format(m__)] = (
                    self.lrg.calc(std, "Ef_Ex_PU_Prf3")(
                        self.d["ef_pu_prf_env_{}".format(m__)][std - 1],
                        self.d["ufd_pu_prf_env_{}".format(m__)][std]))

                std_ex_strn = self.lrg.calc(std, "Std_Ex_Strn1")(
                    self.d["ef_pu_prf_env_{}".format(m__)][std],
                    self.d["ufd_pu_prf_env_{}".format(m__)][std])

                # 计算比例凸度包络线上下限
                self.d.loc[std, "pu_prf_env_{}".format(m__)] = (
                    self.lrg.calc(std, "Istd_Ex_PU_Prf0")(
                        std_ex_strn,
                        self.d["ef_pu_prf_env_{}".format(m__)][std]))

            # 检查确认
            parameter_list = [
                "pu_prf_env",
                "ef_pu_prf_env",
                "ufd_pu_prf_env",
                "force_pu_wid_env"]

            for para in parameter_list:
                scratch = max(
                    self.d["{}_min".format(para)][std],
                    self.d["{}_max".format(para)][std])

                self.d["{}_min".format(para)][std] = min(
                    self.d["{}_min".format(para)][std],
                    self.d["{}_max".format(para)][std])

                self.d["{}_max".format(para)][std] = scratch

            # 迭代计数器处理
            if 7 == std:
                break
            else:
                std = std + 1
