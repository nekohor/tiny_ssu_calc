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

coil_id = "M18104265M"
# coil_id = "M18104265M_40"
coil_id = "M18104948C"
# coil_id = "M18029002C"
# coil_id = "M18104946C"
coil_id = "M18112021H"
coil_id = "M18122789C"

lock_list = pd.Series((np.nan,) * 7, index=[1, 2, 3, 4, 5, 6, 7])
lock_list[1] = np.nan
lock_list[2] = np.nan
lock_list[3] = np.nan
lock_list[4] = np.nan
lock_list[5] = np.nan
lock_list[6] = np.nan
lock_list[7] = np.nan

# lock_list[1] = -140
# lock_list[2] = 10
# lock_list[3] = 30
# lock_list[4] = 40
# lock_list[5] = 50
# lock_list[6] = np.nan
# lock_list[7] = np.nan
print(lock_list)

fsstd = FSStd(coil_id, setting.SAMPLE_DIR)

lpce = LateralPiece(fsstd)
lrg = LateralRollGap(fsstd, lpce)
ufd = UniForcDist(fsstd)
crlc = CompositeRollStackCrown(fsstd)

# prepare initial crlc crn and lock shft pos
fsstd.last_crlc_crn(crlc)
fsstd.lock_pos_shft(lock_list)

penv = ProfileEnvelope(fsstd, lpce, lrg, ufd, crlc)
penv.Calculate()

alc = Allocation(fsstd, lpce, lrg, ufd, crlc, penv)
alc.Calculate()

penv.d.to_excel("penv_result.xlsx")
print("========================lpce and lrg==============================")
print(lpce.d)
print(lrg.d)
print("=====================penv==================================")
print(penv.d)
print("=====================alc==================================")
print(lpce.d[["ufd_pu_prf", "ef_pu_prf", "strn", "prf"]])
# print(alc.d)
print(fsstd.lim[["wr_shft_lim_min", "wr_shft_lim_max"]])
fsstd.d.loc[6, "wr_shft_last"] = 0
fsstd.d.loc[7, "wr_shft_last"] = 0
print(fsstd.d[["wr_shft_last", "wr_shft", "force_bnd_des", "force_bnd"]])
# print(crlc.d)
