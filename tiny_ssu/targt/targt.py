


class Targt():


    def __init__(self):
        pass


    def Limit_PU_Prf(self,pu_prf_buf,targ_same):
        pu_prf = mathuty.Clamp(
            pu_prf_buf,
            pu_prf_lim["min"],
            pu_prf_lim["max"])