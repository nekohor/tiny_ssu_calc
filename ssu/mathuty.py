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


def clamp(n, small, large):
    return max(small, min(n, large))


def clamp_old(aim_val, min_val, max_val):
    if aim_val <= min_val:
        return min_val
    elif aim_val >= max_val:
        return max_val
    else:
        return aim_val
