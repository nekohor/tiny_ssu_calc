# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import global_setting as setting
import logging
logging.basicConfig(level=logging.INFO, filename="print.log")


class UniForcDist():

    def __init__(self, input_df):
        # 机架向量准备
        self.std_vec = np.array([1, 2, 3, 4, 5, 6, 7])
        # 输入的dataframe
        self.input_df = input_df
        # ufd gain perparation
        self.gain_interp_df = pd.read_excel(
            setting.CFG_DIR +
            "cfg_ufd/ufd_partial_derivertive_%d.xlsx" % setting.ROLL_LINE)
        self.gain_mult_df = pd.DataFrame(index=self.std_vec)
        self.c_cof = pd.read_excel(
            setting.CFG_DIR +
            "cfg_ufd/c_cof_%d.xlsx" % setting.ROLL_LINE)
        self.b_cof = pd.DataFrame()
        self.wrbr_df = pd.read_excel(
            setting.CFG_DIR +
            "cfg_ufd/wrbr_para_%d.xlsx" % setting.ROLL_LINE)

        self.init()

    @staticmethod
    def ssuIdx(std):
        if std in [1, 2, 3, 4]:
            return 0
        elif std in [5, 6, 7]:
            return 1
        else:
            raise Exception()

    def init(self):
        # ufd gain mult clacs ,note that "mult" not gain instead
        dd_list = ["dp_dbnd", "dp_dfrcw", "dp_dpcwr", "dp_dwrbr"]
        for dd in dd_list:
            self.gain_mult_df["%s_mul" % dd] = [
                np.interp(
                    input_df["en_width"][std],
                    self.gain_interp_df["pce_wid_vec"],
                    self.gain_interp_df["%s_%d" %
                                        (dd, UniForcDist.ssuIdx(std))]
                ) for std in self.std_vec
            ]

        # base b_cof[0..17] calcs
        for std in self.std_vec:
            idx = UniForcDist.ssuIdx(std)
            width = self.input_df["en_width"][std]
            self.b_cof[std] = ((
                self.c_cof["c0_%d" % idx] +
                self.c_cof["c1_%d" % idx] * width +
                self.c_cof["c2_%d" % idx] * pow(width, 2) +
                self.c_cof["c3_%d" % idx] * pow(width, 3)
            ) * pow(
                ((width - 2 * setting.distEdge) / width), 2)
            )

        # ----last b_cof_martix[0..17] calcs----
        # wr_len = rollpara.loc["length", "wr"]
        br_len = self.wrbr_df.loc["length", "br"]
        wr_wid = self.wrbr_df.loc["width", "wr"]
        br_wid = self.wrbr_df.loc["width", "br"]

        for std in self.std_vec:
            # 局部指针优化
            dp_dbnd_mul = self.gain_mult_df.loc[std, "dp_dbnd_mul"]
            dp_dfrcw_mul = self.gain_mult_df.loc[std, "dp_dfrcw_mul"]
            dp_dpcwr_mul = self.gain_mult_df.loc[std, "dp_dpcwr_mul"]
            dp_dwrbr_mul = self.gain_mult_df.loc[std, "dp_dwrbr_mul"]

            avg_diam_wr = input_df["avg_diam_wr"][std]
            avg_diam_br = input_df["avg_diam_br"][std]
            equiv_mod_wr = input_df["equiv_mod_wr"][std]

            self.b_cof.loc[0, std] *= dp_dfrcw_mul
            self.b_cof.loc[1, std] *= dp_dfrcw_mul
            self.b_cof.loc[2, std] *= (dp_dpcwr_mul * pow(br_len / wr_wid, 2))
            self.b_cof.loc[3, std] *= (
                dp_dfrcw_mul * dp_dwrbr_mul * pow(br_len / br_wid, 2))
            self.b_cof.loc[4, std] *= (
                dp_dfrcw_mul * dp_dwrbr_mul * pow(br_len / br_wid, 2))
            self.b_cof.loc[5, std] *= dp_dbnd_mul
            self.b_cof.loc[6, std] *= dp_dfrcw_mul * dp_dbnd_mul
            self.b_cof.loc[7, std] *= dp_dfrcw_mul * dp_dbnd_mul
            self.b_cof.loc[8, std] *= dp_dwrbr_mul * pow(br_len / br_wid, 2)
            self.b_cof.loc[9, std] *= avg_diam_wr * dp_dfrcw_mul
            self.b_cof.loc[10, std] *= avg_diam_wr * dp_dbnd_mul
            self.b_cof.loc[11, std] *= avg_diam_br * dp_dfrcw_mul
            self.b_cof.loc[12, std] *= equiv_mod_wr * dp_dfrcw_mul
            self.b_cof.loc[13, std] *= equiv_mod_wr * dp_dbnd_mul
            self.b_cof.loc[14, std] *= (
                avg_diam_wr * dp_dpcwr_mul * pow(br_len / wr_wid, 2))
            self.b_cof.loc[15, std] *= (
                equiv_mod_wr * dp_dpcwr_mul * pow(br_len / wr_wid, 2))
            self.b_cof.loc[16, std] *= avg_diam_wr * avg_diam_br
            self.b_cof.loc[17, std] *= avg_diam_br * equiv_mod_wr

    def Dprf_Dfrcw(b_cof, std, input_df, lim_df):
        return (b_cof[std][0] +
                b_cof[std][9] +
                b_cof[std][11] +
                (b_cof[std][3] +
                    1.5 * b_cof[std][4] * pow(input_df["force_pu_wid"], 0.5)) *
                lim_df["wr_br_crn_nom"] +
                (b_cof[std][6] +
                    2 * b_cof[std][7] * input_df["force_pu_wid"]) *
                lim_df["force_bnd_nom"] +
                1.5 * (b_cof[std][1] + b_cof[std][12]) *
                pow(input_df["force_pu_wid"], 0.5))

    def Prf():
        """
        Prf的设计必须能够保证无论是传向量进来还是传值进来，都能计算，因此这里仅仅是
        数据的计算过程
        """
        pass

    def Crns(self,
             std,
             ufd_prf,
             force_pu_wid,
             force_bnd,
             pce_wr_crn,
             wr_br_crn
             ):
        ufd_prf_buf = self.Prf(force_pu_wid,
                               force_bnd,
                               pce_wr_crn,
                               wr_br_crn)
        wr_wid = self.wrbr_df.loc["width", "wr"]
        br_wid = self.wrbr_df.loc["width", "br"]
        brwr_mul = pow(br_wid / wr_wid, 2)
        wr_crn_chg = (
            # (ufd_prf - ufd_prf_buf / ufd_modifier) /
            (ufd_prf - ufd_prf_buf) /
            (self.b_cof.loc[2, std] +
             self.b_cof.loc[14, std] +
             self.b_cof.loc[15, std] +
             (self.b_cof.loc[3, std] * force_pu_wid +
                self.b_cof.loc[4, std] * pow(force_pu_wid, 1.5) +
                self.b_cof.loc[8, std]) * brwr_mul)
        )
        pce_wr_crn_buf = pce_wr_crn + wr_crn_chg
        wr_br_crn_buf = wr_br_crn + wr_crn_chg * brwr_mul
        return pce_wr_crn_buf, wr_br_crn_buf

    def ufd_modifier(std):
        pass

    def Prf(self,
            std,
            force_pu_wid, force_bnd,
            pce_wr_crn, wr_br_crn):
        return (
            self.b_cof.loc[0, std] * force_pu_wid +
            self.b_cof.loc[1, std] * force_pu_wid ** 1.5 +
            self.b_cof.loc[2, std] * pce_wr_crn +
            self.b_cof.loc[3, std] * wr_br_crn * force_pu_wid +
            self.b_cof.loc[4, std] * wr_br_crn * force_pu_wid ** 1.5 +
            self.b_cof.loc[5, std] * force_bnd +
            self.b_cof.loc[6, std] * force_bnd * force_pu_wid +
            self.b_cof.loc[7, std] * force_bnd * force_pu_wid ** 2 +
            self.b_cof.loc[8, std] * wr_br_crn +
            self.b_cof.loc[9, std] * force_pu_wid +
            self.b_cof.loc[10, std] * force_bnd +
            self.b_cof.loc[11, std] * force_pu_wid +
            self.b_cof.loc[12, std] * force_pu_wid ** 1.5 +
            self.b_cof.loc[13, std] * force_bnd +
            self.b_cof.loc[14, std] * pce_wr_crn +
            self.b_cof.loc[15, std] * pce_wr_crn +
            self.b_cof.loc[16, std] + self.b_cof.loc[17, std]
        ) * self.ufd_modifier(std)

    def Pce_WR_Crn(self, std, ufd_prf, force_pu_wid, force_bnd, wr_br_crn):
        std_col = "F%d" % std
        return ((ufd_prf / self.ufd_modifier(std) -
                 self.b_cof.loc[0, std_col] * force_pu_wid -
                 self.b_cof.loc[1, std_col] * force_pu_wid ** 1.5 -
                 self.b_cof.loc[3, std_col] * wr_br_crn * force_pu_wid -
                 self.b_cof.loc[4, std_col] * wr_br_crn * force_pu_wid ** 1.5 -
                 self.b_cof.loc[5, std_col] * force_bnd -
                 self.b_cof.loc[6, std_col] * force_bnd * force_pu_wid -
                 self.b_cof.loc[7, std_col] * force_bnd * force_pu_wid ** 2 -
                 self.b_cof.loc[8, std_col] * wr_br_crn -
                 self.b_cof.loc[9, std_col] * force_pu_wid -
                 self.b_cof.loc[10, std_col] * force_bnd -
                 self.b_cof.loc[11, std_col] * force_pu_wid -
                 self.b_cof.loc[12, std_col] * force_pu_wid ** 1.5 -
                 self.b_cof.loc[13, std_col] * force_bnd -
                 self.b_cof.loc[16, std_col] -
                 self.b_cof.loc[17, std_col]) /
                (self.b_cof.loc[2, std_col] + self.b_cof.loc[14, std_col] +
                    self.b_cof.loc[15, std_col]))


if __name__ == '__main__':
    input_df = pd.DataFrame(index=[1, 2, 3, 4, 5, 6, 7])
    input_df["en_width"] = np.array([1300] * 7)
    input_df["equiv_mod_wr"] = (
        [185800, 182700, 182000, 181500, 191100, 192300, 195300])
    input_df["avg_diam_wr"] = (
            [822.33, 780.22, 771.71, 766.32, 632.51, 650.03, 698.41])
    input_df["avg_diam_br"] = (
            [1485.39, 1467.4, 1508.8, 1532.64, 1571.28, 1520.01, 1487.32])

    ufd = UniForcDist(input_df)
    print(ufd.gain_mult_df)
    print(ufd.b_cof)
