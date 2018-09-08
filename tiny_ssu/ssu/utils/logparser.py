# coding:utf-8
import pandas as pd
import os
import re


class LogParser():

    def __init__(self, root_dir, coil_id, coil_dir):
        self.root_dir = root_dir

        self.line = self.judge_line(coil_id)
        self.coil_id = coil_id
        self.coil_dir = coil_dir

        self.kind = "ssu"
        self.suffix = "cx"

    def judge_line(self, coil_id):
        if coil_id.startswith("M"):
            return 1580
        elif coil_id.startswith("H"):
            return 2250
        else:
            raise Exception("wrong roll line")

    def pattern_file_name(self):
        if self.kind == "ssu":
            return (
                self.root_dir +
                '/utils/pattern/{}/shape_pattern{}_{}.txt'
                .format(self.line, self.line, self.suffix))

    def log_file_name(self):
        return (self.coil_dir +
                '/{}_{}_{}.txt'.format(
                    self.kind, self.coil_id, self.suffix))

    def compile_pattern(self, pf_name):
        pattern_list = []
        with open(pf_name, 'r') as pf:
            for p in pf.readlines():
                # 因为没有对字符串p加r，
                # 所以模式文件中的正则项目如果用到\,需要打两个。
                pattern_list.append(re.compile(p))
        return pattern_list

    def parse_data(self, logf_name):
        ss = pd.Series()
        with open(logf_name, 'r') as sf:
            for p in self.p_list:
                s = sf.readline()
                if s.startswith("|"):
                    continue
                if s.startswith("!"):
                    continue
                mobj = p.match(s)
                print(p)
                print(s)
                if mobj.groups == ():
                    continue
                else:
                    # tag = "\<(.*?)\>"
                    print(mobj.groupdict())
                    for k, v in mobj.groupdict().items():
                        ss[k] = v
        return ss

    def run_by_re(self, result_dir):
        self.p_list = self.compile_pattern(self.pattern_file_name())
        self.ss = self.parse_data(self.log_file_name())

        dest_dir = "/".join([result_dir, self.coil_id])
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        restruct = ReStruct(self.ss, dest_dir)
        return restruct
        restruct.struct_input_df()
        restruct.struct_crn_stk_df()

    def run_by_idx(self):
        pass


class ReStruct():
    def __init__(self, ss, dest_dir):
        self.std_vec = [1, 2, 3, 4, 5, 6, 7]
        self.pass_vec = [0, 1, 2, 3, 4, 5, 6, 7]
        self.ss = ss
        self.dest_dir = dest_dir

    def struct_input_df(self):
        result = pd.DataFrame()

        for std in self.std_vec:
            result.loc[std, "en_width"] = self.ss["Width_Bar"]
            result.loc[std, "ex_width"] = self.ss["Width_Bar"]

        for std in self.std_vec[1:]:
            result.loc[std, "en_thick"] = (
                self.ss["Pce_Thck_Req_{}".format(std - 1)])
        result.loc[1, "en_thick"] = self.ss["Thick_Bar"]

        diff_dict = {
            "ex_thick": "Pce_Thck_Req_{}",
            "rolling_force": "Force_Sup_{}",
            "ex_temp": "Pce_Temp_Sup_{}",
            "ex_tension": "Ten_Stress_Sup_{}",
            "avg_diam_wr": "WR_Avg_Dia_{}",
            "avg_diam_br": "BR_Avg_Dia_{}",
            "equiv_mod_wr": "WR_Eqv_Elas_Mod_{}",
            "prf_chg_attn_fac": "Attn_Fac_{}"
        }

        for std in self.std_vec:
            for k, v in diff_dict.items():
                result.loc[std, k] = self.ss[v.format(std)]

        result["pu_prf_pass0"] = self.ss["Ef_PU_Prf_Alc_0"]
        output_file_name = (
            self.dest_dir + "/{}_input_df.xlsx".format(self.ss["Product_ID"]))
        result.to_excel(output_file_name)
        return pd.read_excel(output_file_name)

    def struct_crn_stk_df(self):
        result = pd.DataFrame()
        diff_dict = {
            "pce_wr_cr": "Pce_WR_Gap_{}",
            "wr_br_cr": "WR_BR_Gap_{}",
            "pce_wr_w_cr": "Pce_WR_Wear_{}",
            "br_w_cr": "BR_Wear_{}",
            "wr_br_w_cr": "WR_BR_Wear_{}",
            "pce_wr_t_cr": "Pce_WR_Thrm_{}",
            "wr_br_t_cr": "WR_BR_Thrm_{}",
            "wr_grn_cr": "WR_Grnd_{}",
            "br_grn_cr": "BR_Grnd_{}",
            "wr_eqv_cr": "WR_Eqv_{}",
            "wr_cr_vrn": "WR_Vern_{}",
            "wr_cr_off": "WR_Offs_{}"
        }
        for std in self.std_vec:
            for k, v in diff_dict.items():
                result.loc[std, k] = self.ss[v.format(std)]

        output_file_name = (
            self.dest_dir +
            "/{}_crn_stk.xlsx".format(self.ss["Product_ID"]))
        result.to_excel(output_file_name)
        return pd.read_excel(output_file_name)
