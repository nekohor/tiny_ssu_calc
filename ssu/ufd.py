# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import global_setting as setting
import logging
logging.basicConfig(level=logging.INFO, filename="print.log")


# 错误类
class OutOfRangeError(BaseException):
    pass


# 输入类函数
def pcEnPceD_width_input():
    return np.array([1200] * 7)


def equiv_mod_wr_input():
    return np.array(
        [185800, 182700, 182000, 181500, 191100, 192300, 195300]
    )


def avg_diam_wr_input():
    return np.array(
        [822.33, 780.22, 771.71, 766.32, 632.51, 650.03, 698.41]
    )


def avg_diam_br_input():
    return np.array(
        [1485.39, 1467.4, 1508.8, 1532.64, 1571.28, 1520.01, 1487.32]
    )


# 辅助类函数
def ssuIdx(std):
    if std in [1, 2, 3, 4]:
        return 0
    elif std in [5, 6, 7]:
        return 1
    else:
        raise Exception()


def std_col(std):
    return "F{}".format(std)


def Dprf_Dfrcw(b_cof, std, input_df, lim_df):
    return (b_cof[std][0] +
            b_cof[std][9] +
            b_cof[std][11] +
            (b_cof[std][3] +
             1.5 * b_cof[std][4] * pow(input_df["force_pu_wid"], 0.5)) * lim_df["wr_br_crn_nom"] +
            (b_cof[std][6] + 2 * b_cof[std][7] * input_df["force_pu_wid"]) * lim_df["force_bnd_nom"] +
            1.5 * (b_cof[std][1] + b_cof[std][12]) *
            pow(input_df["force_pu_wid"], 0.5))


def init(input_df):
    # 机架向量准备
    std_vec = np.array([1, 2, 3, 4, 5, 6, 7])

    # 变化的输入量
    width_vec = input_df[""]
    equiv_mod_wr_vec = equiv_mod_wr_input()
    avg_diam_wr_vec = avg_diam_wr_input()
    avg_diam_br_vec = avg_diam_br_input()

    # dxx_dxx_mul clacs
    dd_para = pd.read_excel(
        setting.CFG_DIR +
        "cfg_ufd/ufd_partial_derivertive_%d.xlsx" % setting.ROLL_LINE)

    pce_wid_vec = dd_para["pce_wid_vec"]
    ddmul_df = pd.DataFrame(index=std_vec)
    dd_list = ["dp_dbnd", "dp_dfrcw", "dp_dpcwr", "dp_dwrbr"]
    for dd in dd_list:
        ddmul_df["%s_mul" % dd] = [
            np.interp(
                width_vec[std - 1], pce_wid_vec,
                dd_para["%s_%d" % (dd, ssuIdx(std))]
            )
            for std in std_vec
        ]
    print(ddmul_df)

    # base b_cof[0..17] calcs
    c_cof = pd.read_excel(
        setting.CFG_DIR +
        "cfg_ufd/c_cof_%d.xlsx" % setting.ROLL_LINE)
    b_cof_df = pd.DataFrame()
    distEdge = 40
    for std in std_vec:
        std_col = "F%d" % std
        b_cof_df[std_col] = (
            (
                c_cof["c0_%d" % ssuIdx(std)] +
                c_cof["c1_%d" % ssuIdx(std)] * width_vec[std - 1] +
                c_cof["c2_%d" % ssuIdx(std)] * pow(width_vec[std - 1], 2) +
                c_cof["c3_%d" % ssuIdx(std)] * pow(width_vec[std - 1], 3)
            ) * pow(
                ((width_vec[std - 1] - 2 * distEdge) / width_vec[std - 1]),
                2)
        )
    print(b_cof_df)

    # ----last b_cof[0..17] calcs----
    rollpara = pd.read_excel(
        setting.CFG_DIR +
        "cfg_ufd/wrbr_para_%d.xlsx" % setting.ROLL_LINE)

    # wr_len = rollpara.loc["length", "wr"]
    br_len = rollpara.loc["length", "br"]
    wr_wid = rollpara.loc["width", "wr"]
    br_wid = rollpara.loc["width", "br"]

    for std in std_vec:
        # 局部指针优化
        std_col = std
        std_idx = std - 1
        dp_dbnd_mul = ddmul_df.loc[std_idx, "dp_dbnd_mul"]
        dp_dfrcw_mul = ddmul_df.loc[std_idx, "dp_dfrcw_mul"]
        dp_dpcwr_mul = ddmul_df.loc[std_idx, "dp_dpcwr_mul"]
        dp_dwrbr_mul = ddmul_df.loc[std_idx, "dp_dwrbr_mul"]

        avg_diam_wr = avg_diam_wr_vec[std_idx]
        avg_diam_br = avg_diam_br_vec[std_idx]
        equiv_mod_wr = equiv_mod_wr_vec[std_idx]

        b_cof.loc[0, std_col] *= dp_dfrcw_mul
        b_cof.loc[1, std_col] *= dp_dfrcw_mul
        b_cof.loc[2, std_col] *= (dp_dpcwr_mul * pow(br_len / wr_wid, 2))
        b_cof.loc[3, std_col] *= (
            dp_dfrcw_mul * dp_dwrbr_mul * pow(br_len / br_wid, 2))
        b_cof.loc[4, std_col] *= (
            dp_dfrcw_mul * dp_dwrbr_mul * pow(br_len / br_wid, 2))
        b_cof.loc[5, std_col] *= dp_dbnd_mul
        b_cof.loc[6, std_col] *= dp_dfrcw_mul * dp_dbnd_mul
        b_cof.loc[7, std_col] *= dp_dfrcw_mul * dp_dbnd_mul
        b_cof.loc[8, std_col] *= dp_dwrbr_mul * pow(br_len / br_wid, 2)
        b_cof.loc[9, std_col] *= avg_diam_wr * dp_dfrcw_mul
        b_cof.loc[10, std_col] *= avg_diam_wr * dp_dbnd_mul
        b_cof.loc[11, std_col] *= avg_diam_br * dp_dfrcw_mul
        b_cof.loc[12, std_col] *= equiv_mod_wr * dp_dfrcw_mul
        b_cof.loc[13, std_col] *= equiv_mod_wr * dp_dbnd_mul
        b_cof.loc[14, std_col] *= (
            avg_diam_wr * dp_dpcwr_mul * pow(br_len / wr_wid, 2))
        b_cof.loc[15, std_col] *= (
            equiv_mod_wr * dp_dpcwr_mul * pow(br_len / wr_wid, 2))
        b_cof.loc[16, std_col] *= avg_diam_wr * avg_diam_br
        b_cof.loc[17, std_col] *= avg_diam_br * equiv_mod_wr
    print(b_cof)


def ufd_modifier(std):
    pass


def Prf(b_cof, std, force_pu_wid, force_bnd, pce_wr_crn, wr_br_crn):
    std_col = "F%d" % std
    cUFDD_Prf = (
        b_cof.loc[0, std_col] * force_pu_wid +
        b_cof.loc[1, std_col] * force_pu_wid ^ 1.5 +
        b_cof.loc[2, std_col] * pce_wr_crn +
        b_cof.loc[3, std_col] * wr_br_crn * force_pu_wid +
        b_cof.loc[4, std_col] * wr_br_crn * force_pu_wid ^ 1.5 +
        b_cof.loc[5, std_col] * force_bnd +
        b_cof.loc[6, std_col] * force_bnd * force_pu_wid +
        b_cof.loc[7, std_col] * force_bnd * force_pu_wid ^ 2 +
        b_cof.loc[8, std_col] * wr_br_crn +
        b_cof.loc[9, std_col] * force_pu_wid +
        b_cof.loc[10, std_col] * force_bnd +
        b_cof.loc[11, std_col] * force_pu_wid +
        b_cof.loc[12, std_col] * force_pu_wid ^ 1.5 +
        b_cof.loc[13, std_col] * force_bnd +
        b_cof.loc[14, std_col] * pce_wr_crn +
        b_cof.loc[15, std_col] * pce_wr_crn +
        b_cof.loc[16, std_col] + b_cof.loc[17, std_col]
    )

    cUFDD_Prf = cUFDD_Prf * ufd_modifier(std)
    return cUFDD_Prf


def Pce_WR_Crn(b_cof, std, ufd_prf, force_pu_wid, force_bnd, wr_br_crn):
    std_col = "F%d" % std
    return ((ufd_prf / ufd_modifier(std) -
             b_cof.loc[0, std_col] * force_pu_wid -
             b_cof.loc[1, std_col] * force_pu_wid ** 1.5 -
             b_cof.loc[3, std_col] * wr_br_crn * force_pu_wid -
             b_cof.loc[4, std_col] * wr_br_crn * force_pu_wid ** 1.5 -
             b_cof.loc[5, std_col] * force_bnd -
             b_cof.loc[6, std_col] * force_bnd * force_pu_wid -
             b_cof.loc[7, std_col] * force_bnd * force_pu_wid ** 2 -
             b_cof.loc[8, std_col] * wr_br_crn -
             b_cof.loc[9, std_col] * force_pu_wid -
             b_cof.loc[10, std_col] * force_bnd -
             b_cof.loc[11, std_col] * force_pu_wid -
             b_cof.loc[12, std_col] * force_pu_wid ** 1.5 -
             b_cof.loc[13, std_col] * force_bnd -
             b_cof.loc[16, std_col] -
             b_cof.loc[17, std_col]) /
            (b_cof.loc[2, std_col] + b_cof.loc[14, std_col] +
                b_cof.loc[15, std_col]))


if __name__ == '__main__':

    print(init())
