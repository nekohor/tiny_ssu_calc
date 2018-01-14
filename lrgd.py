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


def Istd_Ex_PU_Prf0(strn_rlf_cof,
                    std_ex_strn,
                    ef_ex_pu_prf):
    """
    calculate interstand exit pu prf for single stand
    IN strn_rlf_cof   or strn_rlf_cof_vec[std]
    IN std_ex_strn
    IN ef_ex_pu_prf
    """
    return ef_ex_pu_prf + std_ex_strn * (1 - strn_rlf_cof)


def Std_Ex_Strn1(pce_infl_cof,
                 prf_chg_attn_fac,
                 ef_en_pu_prf,
                 ufd_pu_prf):
    """
    calculate std_ex_strn by ef_en_pu_prf and ufd_pu_prf
    for single stand
    IN pce_infl_cof or pce_infl_cof_vec[std]
    IN prf_chg_attn_fac or prf_chg_attn_fac_vec[std]
    IN ef_en_pu_prf
    IN ufd_pu_prf
    """
    return pce_infl_cof * (ufd_pu_prf - ef_en_pu_prf) / prf_chg_attn_fac