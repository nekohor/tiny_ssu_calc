# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

import global_setting as setting
import mathuty

import logging
logging.basicConfig(level=logging.INFO, filename="print.log")


class CompositeRollStackCrown(object):
    """docstring for COMPOSITE ROLL STACK CROWN"""

    def __init__(self, input_df):
        self.input_df = input_df
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

    def Shft_Pos(self,
                 std,
                 pce_wr_cr_req,
                 pce_wr_cr_org,
                 lim_df,
                 pos_shft_input):
        pos_shft_org = pos_shft_input
        rprof = self.profile_df["rprof"][std]
        if "cvc" == rprof[:3]:
            # wr_grn_cr的计算还有一种方式@@2ND-2(MAC005)
            wr_grn_cr = np.interp(
                pos_shft_org,
                self.interp_df["cvc_shft_vec"],
                self.interp_df["cvc_cr_mat_{}".format(rprof)]
            )
        else:
            return pos_shft_org
        pce_wr_cr_dlt = pce_wr_cr_req - pce_wr_cr_org
        wr_grn_cr_req = wr_grn_cr + pce_wr_cr_dlt / 2
        pos_shft = np.interp(
            wr_grn_cr_req,
            self.interp_df["cvc_cr_mat_{}".format(rprof)],
            self.interp_df["cvc_shft_vec"]
        )
        # 限幅
        pos_shft = mathuty.clamp(
            pos_shft,
            lim_df["pos_shft_lim_min"][std],
            lim_df["pos_shft_lim_max"][std]
        )
        # 计算辊系凸度buf1
        pce_wr_cr_buf1, wr_br_cr_buf1 = self.Crns(std, pos_shft)
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
        # 迭代计算
        iter_mx = 15
        pce_wr_cr_tol = 0.01
        for i in range(1, iter_mx + 1):
            pos_shft_dlt = 2
            if (pos_shft + pos_shft_dlt) > lim_df["pos_shft_lim_max"][std]:
                pos_shft_dlt = - pos_shft_dlt
            pos_shft = pos_shft + pos_shft_dlt
            pce_wr_cr_buf2, wr_br_cr_buf2 = self.Crns(std, pos_shft)

            if (((pos_shft_dlt >= 0) & (pce_wr_cr_buf2 <= pce_wr_cr_buf1)) |
                    ((pos_shft_dlt < 0) & (pce_wr_cr_buf2 >= pce_wr_cr_buf1))):

                if pce_wr_cr_req > pce_wr_cr_buf1:
                    pos_shft = pos_shft + pos_shft_dlt
                else:
                    pos_shft = pos_shft - pos_shft_dlt
            else:
                pos_shft = (
                    pos_shft + (pce_wr_cr_req - pce_wr_cr_buf1) *
                    pos_shft_dlt / (pce_wr_cr_buf2 - pce_wr_cr_buf1)
                )
                if (((pos_shft_clmp_min & pos_shft >= pos_shft_lim_max) |
                        (pos_shft_clmp_max & pos_shft <= pos_shft_lim_min))):
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
            # 确认是否达到收敛精度
            if (abs(pce_wr_cr_req - pce_wr_cr_buf1) <= pce_wr_cr_tol):
                break
            if (pce_wr_cr_buf1 > pce_wr_cr_req):
                if pos_shft_clmp_min:
                    break
                else:
                    pos_shft_lim_max = pos_shft
            else:
                if pos_shft_clmp_max:
                    break
                else:
                    pos_shft_lim_min = pos_shft
        pos_shft = mathuty.clamp(pos_shft,
                                 pos_shft_lim_min,
                                 pos_shft_lim_max)
        return pos_shft

    def wr_grn_cr_scalar(self, std, pos_shft):
        """
        CVC equiv crowm
        """
        rprof = self.profile_df["rprof"][std]
        parab_crn = self.profile_df["parab_crn"][std]
        if "cvc" == rprof[:3]:
            # wr_grn_cr的计算还有一种方式@@2ND-2(MAC005)
            wr_grn_cr_buf = np.interp(
                pos_shft,
                self.interp_df["cvc_shft_vec"],
                self.interp_df["cvc_cr_mat_{}".format(rprof)]
            )
        else:  # parab including top and bot roll
            wr_grn_cr_buf = parab_crn[std]
        return wr_grn_cr_buf

    def wr_grn_cr_vector(self, pos_shft_series):
        rprof = self.profile_df["rprof"]
        parab_crn = self.profile_df["parab_crn"]
        cr = pd.Series(index=self.std_vec)
        for std in self.std_vec:
            if "cvc" == rprof[std][:3]:
                # wr_grn_cr的计算还有一种方式@@2ND-2(MAC005)
                cr[std] = np.interp(
                    pos_shft_series[std],
                    self.interp_df["cvc_shft_vec"],
                    self.interp_df["cvc_cr_mat_{}".format(rprof[std])]
                )
            else:  # parab including top and bot roll
                cr[std] = parab_crn[std]
        return cr

    def Crns(self, std, pos_shft):
        ss = self.input_df[std]
        pce_wr_cr_buf = (
            ss["pce_wr_t_cr"] +
            ss["pce_wr_w_cr"] +
            self.wr_grn_cr_scalar(std, pos_shft) +
            ss["wr_crn_vrn"] +
            ss["wr_crn_off"])

        # 支持辊与工作辊长度相对比例系数
        br_len = self.wrbr_df["br"]["length"]
        wr_len = self.wrbr_df["wr"]["length"]
        br_wr_mul = pow(br_len / wr_len, 2)

        wr_br_cr_buf = (
            ss["br_w_cr"] +
            ss["wr_br_t_cr"] +
            ss["wr_br_w_cr"] +
            (self.wr_grn_cr_scalar(std, pos_shft) +
                ss["wr_crn_vrn"] +
                ss["wr_crn_off"]) * br_wr_mul
        )
        return pce_wr_cr_buf, wr_br_cr_buf

    def Crns_vector(self, pos_shft_series):
        input_df = self.input_df
        pce_wr_cr_buf = (
            input_df["pce_wr_t_cr"] +
            input_df["pce_wr_w_cr"] +
            self.wr_grn_cr_vector(pos_shft_series) +
            input_df["wr_crn_vrn"] +
            input_df["wr_crn_off"])

        # 支持辊与工作辊长度相对比例系数
        br_len = self.wrbr_df["br"]["length"]
        wr_len = self.wrbr_df["wr"]["length"]
        br_wr_mul = pow(br_len / wr_len, 2)

        wr_br_cr_buf = (
            input_df["br_w_cr"] +
            input_df["wr_br_t_cr"] +
            input_df["wr_br_w_cr"] +
            (self.wr_grn_cr_vector(pos_shft_series) +
                input_df["wr_crn_vrn"] +
                input_df["wr_crn_off"]) * br_wr_mul
        )
        return pce_wr_cr_buf, wr_br_cr_buf


if __name__ == '__main__':
    cfg = {
        "line": 1580
    }
    std_vec = np.array([1, 2, 3, 4, 5, 6, 7])
    pos_shft_array = pd.Series(
        [-80.6, -3.28, 14.64, 6.06, -91.31, 66.79, 111.34])
    pos_shft_array.index = std_vec

    print(wr_grn_cr(pos_shft_array))
