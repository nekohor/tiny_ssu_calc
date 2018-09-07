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
sys.path.append("e:/box/")

import logging
logging.basicConfig(level=logging.INFO, filename="print.log")

sns.set(color_codes=True)
sns.set(rc={'font.family': [u'Microsoft YaHei']})
sns.set(rc={'font.sans-serif': [u'Microsoft YaHei', u'Arial',
                                u'Liberation Sans', u'Bitstream Vera Sans',
                                u'sans-serif']})


class Allocation():

    def __init__(self, fsstd, evllpce, targt, crlc):
        self.std_vec = [1, 2, 3, 4, 5, 6, 7]
        self.fsstd = fsstd
        self.evllpce = evllpce
        self.targt = targt
        self.crlc = crlc
        self.d = pd.DataFrame()

    def Calculate(self):
        self.d.loc[0, "thick"] = self.fsstd.d.loc[1, "en_thick"]

        for std in self.std_vec:
            self.d.loc[std, "force_pu_wid"] = (
                self.fsstd.d.loc[std, "force_strip"] /
                self.fsstd.d.loc[std, "en_width"])

            self.d.loc[std, "thick"] = self.fsstd.d.loc[std, "ex_thick"]

            # *pcFSPassD->pcAlcD->pcRollbite =
            #     *pcFSPassD->pcFSStdD[ iter ]->pcRollbite;

            # if ( pcFSPassD->pcFSStdD[ iter ]->pcLRGD->pce_infl_cof <= 0.0 )
            # {
            #     pcPceIZFSPassD = pcFSPassD;
            # }

        pu_prf_change_sum = 0
        for std in self.std_vec:
            if self.evllpce.d.loc[std, "strn_rlf_cof"] == 0:
                pu_prf_change_sum += self.fsstd.lrg.d.loc[std, "pce_infl_cof"]
            else:
                pu_prf_change_sum += (
                    self.evllpce.d.loc[std, "strn_rlf_cof"] /
                    self.fsstd.lrg.d.loc[std, "pce_infl_cof"] *
                    self.evllpce.d.loc[std, "elas_modu"])

        self.targt.Delvry_Pass()


def alc_calculate():
    pass
