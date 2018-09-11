from utils.logparser import LogParser
from config.setting import ROOT_DIR


class FSStd():

    def __init__(self, coil_id, log_dir):
        self.coil_id = coil_id
        self.log_dir = log_dir

        lp = LogParser(ROOT_DIR, self.coil_id, self.log_dir)
        rs = lp.run_by_re(self.log_dir)

        self.d = rs.struct_input_df()
        self.crn_stk = rs.struct_crn_stk_df()
        self.lim = rs.struct_lim_df()
