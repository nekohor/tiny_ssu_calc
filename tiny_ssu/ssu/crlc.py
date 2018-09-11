# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from config.setting import CFG_DIR
from config.setting import ROLL_LINE
from utils import mathuty
import logging
logging.basicConfig(level=logging.INFO, filename="crlc_print.log")


class CompositeRollStackCrown(object):

    def __init__(self, fsstd):
        self.fsstd = fsstd

        if fsstd.crn_stk is None:
            self.crn_stk = pd.DataFrame()
        else:
            self.crn_stk = fsstd.crn_stk

        self.std_vec = np.array([1, 2, 3, 4, 5, 6, 7])

        self.cfg_prof = pd.read_excel(
            CFG_DIR + "/cfg_crlc/profile_{}.xlsx".format(ROLL_LINE))
        self.cfg_interp = pd.read_excel(
            CFG_DIR + "/cfg_crlc/wr_grn_cr_interp_{}.xlsx".format(ROLL_LINE))
        self.cfg_wrbr = pd.read_excel(
            CFG_DIR + "/cfg_crlc/wrbr_para_{}.xlsx".format(ROLL_LINE))
        self.cvc_a_cof = pd.DataFrame()   # cvc_a_cof dataframe
        self.d = pd.DataFrame(index=self.std_vec)
        self.Init()

    def Init(self):
        pce_wid = self.pce_wid = self.fsstd.d["en_width"].mean()
        self.d["pce_wid"] = [pce_wid for x in self.std_vec]
        wr_wid = self.wr_wid = self.cfg_wrbr["wr"]["width"]
        br_wid = self.br_wid = self.cfg_wrbr["br"]["width"]
        self.hlf_pce_wid = pce_wid / 2
        self.hlf_br_wid = br_wid / 2
        self.wr_pce_mul = pow((wr_wid / pce_wid), 2)
        self.br_wr_mul = pow((br_wid / wr_wid), 2)

        # cvc position parameter like limitation etc.
        cvc_Sm = self.cvc_Sm = 150
        cvc_width_nominal = 1275
        max_cvc_crn = self.cfg_prof["max_roll_crn"]
        min_cvc_crn = self.cfg_prof["min_roll_crn"]

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

        self.d["cvc_a1"] = self.cvc_a_cof[0]
        self.d["cvc_a2"] = self.cvc_a_cof[1]
        self.d["cvc_a3"] = self.cvc_a_cof[2]

        # Calculated the c1 and c2 for specific width.
        # Cb = -(0.5 * a2 * B * B +
        #        0.75 * a3 * L * B * B -
        #        1.5 * a3 * B * B * s)
        self.d["cvc_crn_wid_min"] = -1 * (
            (0.5 * self.cvc_a_cof[1] * pce_wid * pce_wid) +
            (0.75 * self.cvc_a_cof[2] * wr_wid * pce_wid * pce_wid) -
            (1.5 * self.cvc_a_cof[2] * pce_wid * pce_wid * (0.0 - cvc_Sm))
        )
        self.d["cvc_crn_wid_max"] = -1 * (
            (0.5 * self.cvc_a_cof[1] * pce_wid * pce_wid) +
            (0.75 * self.cvc_a_cof[2] * wr_wid * pce_wid * pce_wid) -
            (1.5 * self.cvc_a_cof[2] * pce_wid * pce_wid * (0.0 + cvc_Sm))
        )

        # If backup roll is CVC roll, then
        # self.profile_df.loc[std, "br_eq_crn_wid"] = (
        #     (getRollCrn(rpos_top, op_backup) * pce_wid * pce_wid) /
        #     (br_wid * br_wid)
        # )

    def Shft_Pos(self, std,
                 pce_wr_cr_req,
                 pos_shft_lim_buf_min,
                 pos_shft_lim_buf_max,
                 pos_shft_org):
        wr_grn_cr = self.wr_grn_crn_single(std, pos_shft_org)

        pce_wr_cr = self.crn_stk["pce_wr_cr"][std]

        pce_wr_cr_dlt = pce_wr_cr_req - pce_wr_cr

        wr_grn_cr_req = wr_grn_cr + (pce_wr_cr_dlt / 2)

        pos_shft = (
            (wr_grn_cr_req -
             ((self.d["cvc_crn_wid_min"][std] +
               self.d["cvc_crn_wid_max"][std]) / 2)) * 2 * self.cvc_Sm
        ) / (self.d["cvc_crn_wid_max"][std] -
             self.d["cvc_crn_wid_min"][std])

        pos_shft = mathuty.Clamp(
            pos_shft,
            pos_shft_lim_buf_min,
            pos_shft_lim_buf_max
        )
        pce_wr_cr_buf1, wr_br_cr_buf1 = self.Crns(std, pos_shft)

        # pos_shft_lim和pos_shft_lim_buf不是一个东西
        # 接下来为pos_shft_lim的赋值计算
        if pce_wr_cr_dlt > 0:
            pos_shft_lim_min = pos_shft_org
            pos_shft_lim_max = pos_shft_lim_buf_max
        else:
            pos_shft_lim_min = pos_shft_lim_buf_min
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
        status = "nonconvgnt"
        iter_mx = 15
        pce_wr_cr_tol = 0.0000001
        for i in range(1, iter_mx + 1):
            pos_shft_dlt = 2
            if (pos_shft + pos_shft_dlt) > pos_shft_lim_buf_max:
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
                status = "valid"
                break
            if (pce_wr_cr_buf1 > pce_wr_cr_req):
                if pos_shft_clmp_min:
                    status = "outofbounds"
                    break
                else:
                    pos_shft_lim_max = pos_shft
            else:
                if pos_shft_clmp_max:
                    status = "outofbounds"
                    break
                else:
                    pos_shft_lim_min = pos_shft

        pos_shft = mathuty.Clamp(pos_shft,
                                 pos_shft_lim_min,
                                 pos_shft_lim_max)
        pce_wr_cr_buf1, wr_br_cr_buf = self.Crns(std, pos_shft)

        print(status)
        return pos_shft

    def Wr_Grn_Crn(self, std, pos_shft):
        rprof = self.cfg_prof["rprof"][std]
        if "cvc" == rprof[:3]:
            # 两只轧辊，两只轧辊，要乘2，要乘2！
            wr_grn_cr_buf = self.wr_grn_crn_single(std, pos_shft) * 2
        else:
            wr_grn_cr_buf = self.cfg_prof["parab_crn"][std]
        return wr_grn_cr_buf

    def wr_grn_crn_single(self, std, pos_shft):
        """single roll"""
        a_cof = self.cvc_a_cof.loc[std]
        pce_wid = self.pce_wid
        wr_wid = self.wr_wid
        return -1 * (
            (0.5 * a_cof[1] * pce_wid * pce_wid) +
            (0.75 * a_cof[2] * wr_wid * pce_wid * pce_wid) -
            (1.5 * a_cof[2] * pce_wid * pce_wid * pos_shft))

    def Crns(self, std, pos_shft):
        ss = self.crn_stk.loc[std]
        pce_wr_cr_buf = (
            ss["pce_wr_t_cr"] +
            ss["pce_wr_w_cr"] +
            self.Wr_Grn_Crn(std, pos_shft) +
            ss["wr_cr_vrn"] +
            ss["wr_cr_off"])

        # 支持辊与工作辊长度相对比例系数
        br_len = self.cfg_wrbr["br"]["length"]
        wr_len = self.cfg_wrbr["wr"]["length"]
        br_wr_mul = pow(br_len / wr_len, 2)
        # print(ss)
        wr_br_cr_buf = (
            ss["br_w_cr"] +
            ss["wr_br_t_cr"] +
            ss["wr_br_w_cr"] +
            ss["br_grn_cr"] +
            (self.Wr_Grn_Crn(std, pos_shft) +
                ss["wr_cr_vrn"] +
                ss["wr_cr_off"]) * br_wr_mul
        )
        return pce_wr_cr_buf, wr_br_cr_buf
