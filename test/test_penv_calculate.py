# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import sys
import os
sys.path.append(os.path.abspath('..'))

import tiny_ssu.ssu as ssu
from ssu.config import setting
from ssu.utils.logparser import LogParser

from ssu.fsstd import FSStd
from ssu.lpce import LateralPiece
from ssu.lrg import LateralRollGap
from ssu.ufd import UniForcDist
from ssu.crlc import CompositeRollStackCrown

from ssu.penv import ProfileEnvelope
import logging
logging.basicConfig(level=logging.INFO, filename="test.log")

print(sys.path[0])
print(os.getcwd())  # 获得当前工作目录
print(os.path.abspath('.'))  # 获得当前工作目录
print(os.path.abspath('..'))  # 获得当前工作目录的父目录
print(os.path.abspath(os.curdir))  # 获得当前工作目录

coil_id = "M18095368M"

fsstd = FSStd(coil_id, setting.SAMPLE_DIR)
penv = ProfileEnvelope(fsstd)
penv.Calculate()

penv.d.to_excel("result.xlsx")
print(penv.func)
