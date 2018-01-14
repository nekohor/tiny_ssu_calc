# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib
from dateutil.parser import parse
from datetime import datetime
import seaborn as sns
import os
import sys
import docx
from docx.shared import Inches
import openpyxl
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
from jinja2 import Environment, PackageLoader
import logging
logging.basicConfig(level=logging.INFO, filename="print.log")

sns.set(color_codes=True)
sns.set(rc={'font.family': [u'Microsoft YaHei']})
sns.set(rc={'font.sans-serif': [u'Microsoft YaHei', u'Arial',
                                u'Liberation Sans', u'Bitstream Vera Sans',
                                u'sans-serif']})


# 辅助函数
def stdIdx(std):
    """
    因为要使用到pass0，所以正在考虑：
    机架的索引到底是遵循计算机规范从0开始，还是遵循工艺规范从1开始？
    """
    return (std - 1)


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
                  pcExPceD_thick_array,
                  pcExPceD_width_array,
                  pcExPceD_tension_array,
                  elas_modu_array
                  ):
    """
    ex width without distEdge
    """
    distEdge = 40
    return (
        crit_bckl_cof(flt_idx) *
        pow(pcExPceD_thick_array / (pcExPceD_width_array - 2 * distEdge), 2) +
        avg_strs_cof(flt_idx) * pcExPceD_tension_array / elas_modu_array)


def update(input_df, *args):
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
    interp_df = pd.read_excel("cfg_lpce/lpce_interp_vec.xlsx")

    para_list = ["elas_modu", "strn_rlf_cof"]
    for para in para_list:
        output_df[para] = [
            np.interp(
                input_df.loc[std, "pcExPceD_temp_avg"],
                interp_df["avg_pce_tmp_interp_vec"],
                interp_df["%s_interp_vec" % para]
            )
            for std in std_vec
        ]

    # 02 --- uptdate bckl_lim ---
    fltmult_df = pd.read_excel(
        "cfg_lpce/sprp_flt_mult_%d.xlsx" % args[0]["line"])

    fltIdx_list = ["we", "cb"]
    for flt_idx in fltIdx_list:
        output_df["bckl_lim_%s" % flt_idx] = (
            crit_bckl_lim(
                flt_idx,
                input_df["pcExPceD_thick"],
                input_df["pcExPceD_width"],
                input_df["pcExPceD_tension"],
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
        "line": 2250
    }
    input_dir = "input_sample/"
    input_df = pd.read_excel(input_dir + "lpce_sample.xlsx")
    print(update(input_df, cfg_dict))
