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


def Cfg_Init(line):
    if line == 2250:
        avg_pce_tmp_vec = np.array(
            [600, 650, 700, 750, 800, 850,
             900, 950, 1000, 1050, 1100, 1500])
        elas_modu_vec = np.array(
            [138269, 128069, 117905, 107751, 97589,
             87415, 77232, 67054, 56909, 46829, 36863, 27067])
        strn_rlf_cof_interp_vec = np.array(
            [0, 0, 0, 0.056, 0.091, 0.16,
             0.303, 0.521, 0.771, 0.968, 0.984, 0.984])
    elif line == 1580:
        avg_pce_tmp_vec = np.array(
            [600, 650, 700, 750, 800, 850,
             900, 950, 1000, 1050, 1100, 1500])
        elas_modu_vec = np.array(
            [138269, 128069, 117905, 107751, 97589,
             87415, 77232, 67054, 56909, 46829, 36863, 27067])
        strn_rlf_cof_interp_vec = np.array(
            [0, 0, 0, 0.056, 0.091, 0.16,
             0.303, 0.521, 0.771, 0.968, 0.984, 0.984])

    else:
        raise Exception()
    return avg_pce_tmp_vec, elas_modu_vec, strn_rlf_cof_interp_vec
