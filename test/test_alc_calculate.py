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
from ssu.alc import Allocation
import logging
logging.basicConfig(level=logging.INFO, filename="test.log")

print(sys.path[0])
print(os.getcwd())  # 获得当前工作目录
print(os.path.abspath('.'))  # 获得当前工作目录
print(os.path.abspath('..'))  # 获得当前工作目录的父目录
print(os.path.abspath(os.curdir))  # 获得当前工作目录

coil_id = "M18095368M"

fsstd = FSStd(coil_id, setting.SAMPLE_DIR)

lpce = LateralPiece(fsstd)
print(lpce.d)
lrg = LateralRollGap(fsstd, lpce)
ufd = UniForcDist(fsstd)
crlc = CompositeRollStackCrown(fsstd)

penv = ProfileEnvelope(fsstd, lpce, lrg, ufd, crlc)
penv.Calculate()

alc = Allocation(fsstd, lpce, lrg, ufd, crlc, penv)
alc.Calculate()

penv.d.to_excel("penv_result.xlsx")
print(lpce.d)
print("====================================")
print(alc.lpce.d)
