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

        self.std_vec = [1, 2, 3, 4, 5, 6, 7]

        self.last_pos_shft()
        # self.last_force_bend()

    def last_pos_shft(self):

        self.d["max_shft"] = [60, 50, 40, 30, 30, 0, 0]
        hard_limit = 140.6

        for std in [1, 2, 3, 4, 5]:
            self.d.loc[std, "wr_shft"] = (
                self.lim["wr_shft_lim_min"][std] + self.d["max_shft"][std])
            if (self.lim["wr_shft_lim_min"][std] + hard_limit) < 1:
                self.d.loc[std, "wr_shft"] = (
                    self.lim["wr_shft_lim_max"][std] - self.d["max_shft"][std])
        self.d.loc[6, "wr_shft"] = self.lim["targ_pos_shft"][6]
        self.d.loc[7, "wr_shft"] = self.lim["targ_pos_shft"][7]

        self.d["wr_shft_last"] = self.d["wr_shft"]

    def last_force_bend(self):
        bnd_list = [444.9, 445.0, 444.9, 444.9, 420.4, 687.8, 338.7]
        self.d["force_bnd"] = [bnd * 2 for bnd in bnd_list]

    def last_crlc_crn(self, crlc):
        for std in self.std_vec:
            tmp = crlc.Crns(std, self.d.loc[std, "wr_shft"])
            self.d.loc[std, "pce_wr_crn_org"] = tmp[0]
            self.d.loc[std, "wr_br_crn_org"] = tmp[1]

    def lock_pos_shft(self, ss):
        self.d["wr_shft_lock"] = ss
