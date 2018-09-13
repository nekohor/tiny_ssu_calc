from fsstd import FSStd
from lpce import LateralPiece
from lrg import LateralRollGap
from ufd import UniForcDist
from crlc import CompositeRollStackCrown

from penv import ProfileEnvelope
from alc import Allocation

class ShapeSetup():

    def __init__(self, fsstd):
        self.fsstd = fsstd


    def Main(self):
        self.redrft_perm = False

        # Initialize_Static_Objects

        # Copy_Object_Chain

        self.Init()

    def Init(self):
        tgt_profile = self.fsstd.d["tgt_profile"].mean()
        tgt_flatness = self.fsstd.d["tgt_flatness"].mean()

        self.lpce = LateralPiece(self.fsstd)
        self.lrg = LateralRollGap(self.fsstd, self.lpce)
        self.ufd = UniForcDist(self.fsstd)
        self.crlc = CompositeRollStackCrown(self.fsstd)


        # Initialize the following dynamic STD quantities
        self.fsstd.d["op_bnd_off"] = (
            self.fsstd.lim["op_bnd_off"]+ self.fsstd.lim["bending_ofs"])

        if self.crlc.cfg_prof["rprof"][7] != "parab":
            self.fsstd.d.loc[7, "force_bnd"] += self.fsstd.d["flt_vrn"].mean()
        



    def Reference(self):
