# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from ..config import setting
from ..utils import mathuty
import logging
logging.basicConfig(level=logging.INFO, filename="crlc_print.log")


class CompositeRollStackCrown(object):
    """docstring for COMPOSITE ROLL STACK CROWN"""

    def __init__(self, input_df, stk_crn_df):
        self.input_df = input_df
        self.stk_crn_df = stk_crn_df
        self.std_vec = np.array([1, 2, 3, 4, 5, 6, 7])

        self.profile_df = pd.read_excel(
            "{}cfg_crlc/profile_df_{}.xlsx".format(
                setting.CFG_DIR, setting.ROLL_LINE))
        self.interp_df = pd.read_excel(
            "{}cfg_crlc/wr_grn_cr_interp_vec_{}.xlsx".format(
                setting.CFG_DIR, setting.ROLL_LINE))
        self.wrbr_df = pd.read_excel(
            "{}cfg_crlc/wrbr_para_{}.xlsx".format(
                setting.CFG_DIR, setting.ROLL_LINE))
        self.cvc_a_cof = pd.DataFrame()   # cvc_a_cof dataframe
        self.crlc_df = pd.DataFrame()
        self.Init()

    def Init(self):
        pce_wid = self.pce_wid = self.input_df["en_width"].mean()
        wr_wid = self.wr_wid = self.wrbr_df["wr"]["width"]
        br_wid = self.br_wid = self.wrbr_df["br"]["width"]
        self.hlf_pce_wid = pce_wid / 2
        self.hlf_br_wid = br_wid / 2
        self.wr_pce_mul = pow((wr_wid / pce_wid), 2)
        self.br_wr_mul = pow((br_wid / wr_wid), 2)

        # cvc position parameter like limitation etc.
        cvc_Sm = self.cvc_Sm = 150
        cvc_width_nominal = 1275
        max_cvc_crn = self.profile_df["MaxRollCrn"]
        min_cvc_crn = self.profile_df["MinRollCrn"]

        # ==========  Calculate a1, a2, a3 from C1 and C2  ==========
        # =====  and nominal width and working roll barrel length.===
        # a2 = ((2Sm - L) * C1 + (2Sm + L) * C2) / (2 * L * L * Sm)
        self.cvc_a_cof[1] = (
            ((2 * cvc_Sm - wr_wid) * min_cvc_crn +
                (2 * cvc_Sm + wr_wid) * max_cvc_crn) /
            (2 * wr_wid * wr_wid * cvc_Sm))

        # a3 = (C1 - C2) / (3 * L * L * sm)
        self.cvc_a_cof[2] = (
            (min_cvc_crn - max_cvc_crn) /
            (3 * wr_wid * wr_wid * cvc_Sm))

        # a1 = -a2 * L - 3 * a3 * (L / 2) * (L / 2) - a3 * B * B / 4
        self.cvc_a_cof[0] = (
            (-self.cvc_a_cof[1] * wr_wid) -
            (3 * self.cvc_a_cof[2] * wr_wid * wr_wid / 4) -
            (self.cvc_a_cof[2] * cvc_width_nominal * cvc_width_nominal / 4))

        # Change it from roll gap crown to roll crown.
        self.cvc_a_cof[0] = - self.cvc_a_cof[0]
        self.cvc_a_cof[1] = - self.cvc_a_cof[1]
        self.cvc_a_cof[2] = - self.cvc_a_cof[2]

        self.crlc_df["cvc_a1"] = self.cvc_a_cof[0]
        self.crlc_df["cvc_a2"] = self.cvc_a_cof[1]
        self.crlc_df["cvc_a3"] = self.cvc_a_cof[2]

        # Calculated the c1 and c2 for specific width.
        # Cb = -(0.5 * a2 * B * B +
        #        0.75 * a3 * L * B * B -
        #        1.5 * a3 * B * B * s)
        self.crlc_df["cvc_crn_wid_min"] = -1 * (
            (0.5 * self.cvc_a_cof[1] * pce_wid * pce_wid) +
            (0.75 * self.cvc_a_cof[2] * wr_wid * pce_wid * pce_wid) -
            (1.5 * self.cvc_a_cof[2] * pce_wid * pce_wid * (0.0 - cvc_Sm))
        )
        self.crlc_df["cvc_crn_wid_max"] = -1 * (
            (0.5 * self.cvc_a_cof[1] * pce_wid * pce_wid) +
            (0.75 * self.cvc_a_cof[2] * wr_wid * pce_wid * pce_wid) -
            (1.5 * self.cvc_a_cof[2] * pce_wid * pce_wid * (0.0 + cvc_Sm))
        )

        # If backup roll is CVC roll, then
        # self.profile_df.loc[std, "br_eq_crn_wid"] = (
        #     (getRollCrn(rpos_top, op_backup) * pce_wid * pce_wid) /
        #     (br_wid * br_wid)
        # )

    def Shft_Pos(self,
                 std,
                 pce_wr_cr_req,
                 pce_wr_cr_org,
                 lim_df,
                 pos_shft_input):
        pos_shft_org = pos_shft_input
        rprof = self.profile_df["rprof"][std]
        if "cvc" == rprof[:3]:
            # --- wr_grn_cr的插值计算方式 ---
            # wr_grn_cr = np.interp(
            #     pos_shft_org,
            #     self.interp_df["cvc_shft_vec"],
            #     self.interp_df["cvc_cr_mat_{}".format(rprof)]
            # )
            # --- 另一种方法@@2ND-2(MAC005) ---
            # Cb = -(0.5 * a2 *B*B + 0.75 * a3 * L *B*B - 1.5 * a3 *B*B * s)
            # 注意是single roll，不要乘2！！！！
            wr_grn_cr = self.wr_grn_cr_single(
                self.cvc_a_cof.loc[std], pos_shft_org)
        else:
            return pos_shft_org
        # pce_wr_cr_org 在原模型中是指penv计算的Crns
        pce_wr_cr_dlt = pce_wr_cr_req - pce_wr_cr_org
        print("init pce_wr_cr_dlt", pce_wr_cr_dlt,
              pce_wr_cr_req, pce_wr_cr_org)
        wr_grn_cr_req = wr_grn_cr + pce_wr_cr_dlt / 2
        # wr_grn_cr_req = wr_grn_cr + pce_wr_cr_dlt

        # pos_shft = np.interp(
        #     wr_grn_cr_req,
        #     self.interp_df["cvc_cr_mat_{}".format(rprof)],
        #     self.interp_df["cvc_shft_vec"]
        # )

        # 不用插值，改用公式  s = (c - (c1+c2)/2 ) * 2 * Sm / ( c2 -c1)
        pos_shft = (
            (wr_grn_cr_req -
             ((self.crlc_df["cvc_crn_wid_min"][std] +
               self.crlc_df["cvc_crn_wid_max"][std]) / 2)) * 2 * self.cvc_Sm
        ) / (self.crlc_df["cvc_crn_wid_max"][std] -
             self.crlc_df["cvc_crn_wid_min"][std])
        # 限幅
        pos_shft = mathuty.clamp(
            pos_shft,
            lim_df["pos_shft_lim_min"][std],
            lim_df["pos_shft_lim_max"][std]
        )
        # 计算辊系凸度buf1
        pce_wr_cr_buf1, wr_br_cr_buf1 = self.Crns(std, pos_shft)
        print("init buf1", pce_wr_cr_buf1)
        # 窜辊位置限制，避免窜辊往期望的负方向移动
        # 注意这里的pos_shft_lim_m__对应源代码中的 pos_shft_lim[ maxl/minl ]
        # 注意lim_df["pos_shft_lim_m__"][std]对应源代码中的 pos_shft_lim_buf[maxl/minl]
        if pce_wr_cr_dlt > 0:
            pos_shft_lim_min = pos_shft_org
            pos_shft_lim_max = lim_df["pos_shft_lim_max"][std]
        else:
            pos_shft_lim_min = lim_df["pos_shft_lim_min"][std]
            pos_shft_lim_max = pos_shft_org
        # 窜辊位置限幅标志位设定
        if pce_wr_cr_buf1 > pce_wr_cr_req:
            pos_shft_lim_max = pos_shft
            pos_shft_clmp_max = True
            pos_shft_clmp_min = False
        else:
            pos_shft_lim_min = pos_shft
            pos_shft_clmp_min = True
            pos_shft_clmp_max = False
        # --- 迭代计算 ---
        iter_mx = 15
        pce_wr_cr_tol = 0.0000001
        for i in range(1, iter_mx + 1):
            pos_shft_dlt = 2
            if (pos_shft + pos_shft_dlt) > lim_df["pos_shft_lim_max"][std]:
                pos_shft_dlt = - pos_shft_dlt
            pce_wr_cr_buf2, wr_br_cr_buf2 = self.Crns(
                std, pos_shft + pos_shft_dlt)

            if (((pos_shft_dlt >= 0) & (pce_wr_cr_buf2 <= pce_wr_cr_buf1)) |
                    ((pos_shft_dlt < 0) & (pce_wr_cr_buf2 >= pce_wr_cr_buf1))):

                if pce_wr_cr_req > pce_wr_cr_buf1:
                    pos_shft = pos_shft + pos_shft_dlt
                    # pos_shft = pos_shft + 2
                else:
                    pos_shft = pos_shft - pos_shft_dlt
                    # pos_shft = pos_shft - 2
            else:
                pos_shft = (
                    pos_shft + (pce_wr_cr_req - pce_wr_cr_buf1) *
                    pos_shft_dlt / (pce_wr_cr_buf2 - pce_wr_cr_buf1)
                )
                if ((pos_shft_clmp_min & (pos_shft >= pos_shft_lim_max)) |
                        (pos_shft_clmp_max & (pos_shft <= pos_shft_lim_min))):
                    pos_shft = (pos_shft_lim_min + pos_shft_lim_max) / 2
            pos_shft_clmp_min = False
            pos_shft_clmp_max = False
            if pos_shft < pos_shft_lim_min:
                pos_shft = pos_shft_lim_min
                pos_shft_clmp_min = True
            if pos_shft > pos_shft_lim_max:
                pos_shft = pos_shft_lim_max
                pos_shft_clmp_max = True
            pce_wr_cr_buf1, wr_br_cr_buf = self.Crns(std, pos_shft)
            print("iter", i, pce_wr_cr_buf1)
            # 确认是否达到收敛精度
            if (abs(pce_wr_cr_req - pce_wr_cr_buf1) <= pce_wr_cr_tol):
                print("valid")
                break
            if (pce_wr_cr_buf1 > pce_wr_cr_req):
                if pos_shft_clmp_min:
                    print("outofbounds")
                    break
                else:
                    pos_shft_lim_max = pos_shft
            else:
                if pos_shft_clmp_max:
                    print("outofbounds")
                    break
                else:
                    pos_shft_lim_min = pos_shft
        pos_shft = mathuty.clamp(pos_shft,
                                 pos_shft_lim_min,
                                 pos_shft_lim_max)
        pce_wr_cr_buf1, wr_br_cr_buf = self.Crns(std, pos_shft)
        return pos_shft

    def wr_grn_cr_single(self, a_cof, pos_shft):
        pce_wid = self.pce_wid
        wr_wid = self.wr_wid
        return -1 * (
            (0.5 * a_cof[1] * pce_wid * pce_wid) +
            (0.75 * a_cof[2] * wr_wid * pce_wid * pce_wid) -
            (1.5 * a_cof[2] * pce_wid * pce_wid * pos_shft))

    def wr_grn_cr_scalar(self, std, pos_shft):
        rprof = self.profile_df["rprof"][std]
        if "cvc" == rprof[:3]:
            # 两只轧辊，两只轧辊，要乘2，要乘2！
            wr_grn_cr_buf = self.wr_grn_cr_single(
                self.cvc_a_cof.loc[std], pos_shft) * 2
        else:
            parab_crn = self.profile_df["parab_crn"][std]
            wr_grn_cr_buf = parab_crn
        return wr_grn_cr_buf

    def wr_grn_cr_vector(self, pos_shft_series):
        rprof = self.profile_df["rprof"]
        parab_crn = self.profile_df["parab_crn"]
        wr_grn_cr_buf = pd.Series(index=self.std_vec)
        for std in self.std_vec:
            if "cvc" == rprof[std][:3]:
                # 两只轧辊，两只轧辊，要乘2，要乘2！
                wr_grn_cr_buf = self.wr_grn_cr_single(
                    self.cvc_a_cof, pos_shft_series) * 2
            else:
                # parab including top and bot roll
                wr_grn_cr_buf[std] = parab_crn[std]
        return wr_grn_cr_buf

    def Crns(self, std, pos_shft):
        ss = self.stk_crn_df.loc[std]
        pce_wr_cr_buf = (
            ss["pce_wr_t_cr"] +
            ss["pce_wr_w_cr"] +
            self.wr_grn_cr_scalar(std, pos_shft) +
            ss["wr_cr_vrn"] +
            ss["wr_cr_off"])

        # 支持辊与工作辊长度相对比例系数
        br_len = self.wrbr_df["br"]["length"]
        wr_len = self.wrbr_df["wr"]["length"]
        br_wr_mul = pow(br_len / wr_len, 2)
        # print(ss)
        wr_br_cr_buf = (
            ss["br_w_cr"] +
            ss["wr_br_t_cr"] +
            ss["wr_br_w_cr"] +
            ss["br_grn_cr"] +
            (self.wr_grn_cr_scalar(std, pos_shft) +
                ss["wr_cr_vrn"] +
                ss["wr_cr_off"]) * br_wr_mul
        )
        return pce_wr_cr_buf, wr_br_cr_buf

    def Crns_vector(self, pos_shft_series):
        stk_crn_df = self.stk_crn_df
        pce_wr_cr_buf = (
            stk_crn_df["pce_wr_t_cr"] +
            stk_crn_df["pce_wr_w_cr"] +
            self.wr_grn_cr_vector(pos_shft_series) +
            stk_crn_df["wr_cr_vrn"] +
            stk_crn_df["wr_cr_off"])

        # 支持辊与工作辊长度相对比例系数
        br_len = self.wrbr_df["br"]["length"]
        wr_len = self.wrbr_df["wr"]["length"]
        br_wr_mul = pow(br_len / wr_len, 2)

        wr_br_cr_buf = (
            stk_crn_df["br_w_cr"] +
            stk_crn_df["wr_br_t_cr"] +
            stk_crn_df["wr_br_w_cr"] +
            stk_crn_df["br_grn_cr"] +
            (self.wr_grn_cr_vector(pos_shft_series) +
                stk_crn_df["wr_cr_vrn"] +
                stk_crn_df["wr_cr_off"]) * br_wr_mul
        )
        return pce_wr_cr_buf, wr_br_cr_buf

    def wr_grn_cr_scalar_old(self, std, pos_shft):
        """
        CVC equiv crowm
        """
        rprof = self.profile_df["rprof"][std]
        if "cvc" == rprof[:3]:
            # wr_grn_cr的计算还有一种方式@@2ND-2(MAC005)
            wr_grn_cr_buf = np.interp(
                pos_shft,
                self.interp_df["cvc_shft_vec"],
                self.interp_df["cvc_cr_mat_{}".format(rprof)]
            ) * 2
        else:
            # parab including top and bot roll
            parab_crn = self.profile_df["parab_crn"][std]
            wr_grn_cr_buf = parab_crn
        return wr_grn_cr_buf
