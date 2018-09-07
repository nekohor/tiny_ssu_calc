# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

from config.setting import DIST_EDGE
import logging
logging.basicConfig(level=logging.INFO, filename="print.log")


class LateralPiece(object):
    """docstring for Latteral"""

    def __init__(self, fsstd):
        # 机架向量准备
        self.std_vec = np.array([1, 2, 3, 4, 5, 6, 7])
        # 输入的dataframe
        self.fsstd = fsstd

        # lpce object df
        self.d = pd.DataFrame(index=self.std_vec)
        # --------------------------------------------------------
        # 插值参数准备
        # 2250和1580产线不同钢种有一样的lpce 插值参数，所以
        # 直接用一个文件，减除一大坨准备函数
        # 若存在产线之间的不同，则修正时也只是载入不同的interp df
        # --------------------------------------------------------
        self.interp_df = pd.read_csv("config/cfg_lpce/lpce_interp.csv")
        # 死区增益准备
        self.flt_mult_df = pd.read_csv("config/cfg_lpce/sprp_flt_mult.csv")
        self.update()

    # --- bckl参数函数 ---
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

    def crit_bckl(
            self,
            flt_idx,
            ex_thick,
            ex_width,
            ex_tension,
            elas_modu):
        """
        ex width without distEdge
        拆分原程序中的Crit_Bckl
        """
        crit_bckl_val = (
            self.crit_bckl_cof(flt_idx) *
            pow(ex_thick / (ex_width - 2 * DIST_EDGE), 2) +
            self.avg_strs_cof(flt_idx) *
            ex_tension / elas_modu
        )
        return crit_bckl_val

    def update(self):
        """
        --- 更新lpce参数的函数 ---
        """
        # 01 --- elas_modu & strn_rlf_cof update ---
        para_list = ["elas_modu", "strn_rlf_cof"]
        for para in para_list:
            self.d[para] = [
                np.interp(
                    self.input_df.loc[std, "ex_temp"],
                    self.interp_df["avg_pce_tmp_interp_vec"],
                    self.interp_df["%s_interp_vec" % para]
                )
                for std in self.std_vec
            ]

        # 02 --- update bckl_lim ---
        flt_idx_list = ["we", "cb"]
        for flt_idx in flt_idx_list:
            self.d["bckl_lim_%s" % flt_idx] = (
                self.crit_bckl(
                    flt_idx,
                    self.input_df["ex_thick"],
                    self.input_df["ex_width"],
                    self.input_df["ex_tension"],
                    self.d["elas_modu"]
                )
            )
            self.d["bckl_lim_%s" % flt_idx] = (
                self.d["bckl_lim_%s" % flt_idx] *
                self.flt_mult_df["sprp_%s_mult" % flt_idx])
