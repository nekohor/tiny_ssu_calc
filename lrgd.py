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


def Istd_Ex_PU_Prf0(std_num, strn_rlf_cof, std_ex_strn, ef_ex_pu_prf):
    """calculate interstand exit pu prf"""
    return ef_ex_pu_prf + std_ex_strn * (1 - strn_rlf_cof(std_num))


def Std_Ex_Strn1(std_num, ef_en_pu_prf, ufd_pu_prf):
    return pce_infl_cof(std_num) * (ufd_pu_prf - ef_en_pu_prf) / prf_chg_attn_fac(std_num)
