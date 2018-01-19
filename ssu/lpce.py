# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import global_setting as setting
import logging
logging.basicConfig(level=logging.INFO, filename="print.log")


# --- bckl参数函数 ---
# 为改善性能，这几个参数直接放在文件里
def avg_strs_cof(flt_idx):
    """
    平均应变系数    flt_idx is we or cb
    average stress coefficient vector
    """
    if flt_idx == "we":
        cof = 1.5
    elif flt_idx == "cb":
        cof = -3.0
    else:
        raise Exception()
    return cof


def crit_bckl_cof(flt_idx):
    """
    flt_idx is we or cb
    为什么边浪的绝对值比中浪的还大呢（80>40）？
    因为产生中浪的应力比边浪小差不多两倍
    piece critical buckling criteria coefficient vector
    """
    if flt_idx == "we":
        cof = 80
    elif flt_idx == "cb":
        cof = -40
    else:
        raise Exception()
    return cof


def crit_bckl_lim(flt_idx,
                  ex_thick_array,
                  ex_width_array,
                  ex_tension_array,
                  elas_modu_array
                  ):
    """
    ex width without distEdge
    """
    distEdge = 40
    return (
        crit_bckl_cof(flt_idx) *
        pow(ex_thick_array / (ex_width_array - 2 * distEdge), 2) +
        avg_strs_cof(flt_idx) * ex_tension_array / elas_modu_array)


def update(input_df, *args, **kwargs):
    """
    --- 更新lpce参数的函数 ---
    """
    # 机架向量准备
    std_vec = np.array([1, 2, 3, 4, 5, 6, 7])

    # updated lpce object df
    output_df = pd.DataFrame(index=std_vec)

    # 01 --- para update ---

    # 插值参数准备
    # 2250和1580产线不同钢种有一样的lpce 插值参数，所以
    # 直接用一个文件，减除一大坨准备函数
    # 若存在产线之间的不同，则修正时也只是载入不同的interp df
    interp_df = pd.read_excel(
        setting.CFG_DIR + "cfg_lpce/lpce_interp_vec.xlsx")

    para_list = ["elas_modu", "strn_rlf_cof"]
    for para in para_list:
        output_df[para] = [
            np.interp(
                input_df.loc[std, "ex_temp"],
                interp_df["avg_pce_tmp_interp_vec"],
                interp_df["%s_interp_vec" % para]
            )
            for std in std_vec
        ]

    # 02 --- update bckl_lim ---
    fltmult_df = pd.read_excel(
        "{}cfg_lpce/sprp_flt_mult_{}.xlsx"
        .format(setting.CFG_DIR, setting.ROLL_LINE))

    fltIdx_list = ["we", "cb"]
    for flt_idx in fltIdx_list:
        output_df["bckl_lim_%s" % flt_idx] = (
            crit_bckl_lim(
                flt_idx,
                input_df["ex_thick"],
                input_df["ex_width"],
                input_df["ex_tension"],
                output_df["elas_modu"]
            )
        )
        output_df["bckl_lim_%s" % flt_idx] = (
            output_df["bckl_lim_%s" % flt_idx] *
            fltmult_df["sprp_%s_mult" % flt_idx]
        )

    return output_df


if __name__ == '__main__':
    cfg_dict = {
        "line": 1580
    }
    input_dir = setting.ROOT_DIR + "input_sample/"
    input_df = pd.read_excel(input_dir + "M18001288W_input_sample.xlsx")
    lpce_df = update(input_df)
    print(lpce_df)
