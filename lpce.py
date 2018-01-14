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
import bushi
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


# 输入函数

# 插值计算参数
def avg_pce_tmp_interp_vec(line):
    if line == 2250:
        vec = np.array(
            [600, 650, 700, 750, 800, 850,
             900, 950, 1000, 1050, 1100, 1500])
    elif line == 1580:
        vec = np.array(
            [600, 650, 700, 750, 800, 850,
             900, 950, 1000, 1050, 1100, 1500])
    else:
        raise Exception()
    return vec


def elas_modu_interp_vec(line):
    if line == 2250:
        vec = np.array(
            [138269, 128069, 117905, 107751, 97589,
             87415, 77232, 67054, 56909, 46829, 36863, 27067])
    elif line == 1580:
        vec = np.array(
            [138269, 128069, 117905, 107751, 97589,
             87415, 77232, 67054, 56909, 46829, 36863, 27067])
    else:
        raise Exception()
    return vec


def strn_rlf_cof_interp_vec(line):
    if line == 2250:
        vec = np.array(
            [0, 0, 0, 0.056, 0.091, 0.16,
             0.303, 0.521, 0.771, 0.968, 0.984, 0.984])
    elif line == 1580:
        vec = np.array(
            [0, 0, 0, 0.056, 0.091, 0.16,
             0.303, 0.521, 0.771, 0.968, 0.984, 0.984])
    else:
        raise Exception()
    return vec


def update():
    # 机架向量准备
    std_vec = np.array([1, 2, 3, 4, 5, 6, 7])

    # list of para
    para_list = ["elas_modu", "strn_rlf_cof"]

    df = pd.DataFrame()
    for para in para_list:
        df["para"] = [
            np.interp(pcExPceD_temp_avg

                      )

            for std in std_vec
        ]

    df.index = std_vec
    pass


if __name__ == '__main__':
    line = 2250
    input_df = pd.DataFrame()
    pcExPceD_temp_avg = pd.Series(
        [1008, 987.4, 968.2, 949, 935.4, 919.3, 912.3])
    # 索引先遵循工艺规范试试看？！
    pcExPceD_temp_avg.index = list(range(1, 8))
    update()
