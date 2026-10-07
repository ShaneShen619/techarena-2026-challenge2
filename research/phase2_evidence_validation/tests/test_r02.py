import sys, unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/phase2_evidence_validation/src'))
from r02 import LoadedTemplate,fit_profile

class R02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.t=LoadedTemplate.from_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz')
    def test_reference_first_root_and_loaded_backsub(self):
        self.assertAlmostEqual(self.t.first_root(),100.412,places=3)
        self.assertAlmostEqual(self.t.voltage([0])[0],self.t.pack_v[0],places=12)
    def test_no_extrapolation_and_unbracketed_root(self):
        with self.assertRaises(ValueError):self.t.voltage([-0.1])
        self.assertIsNone(self.t.first_root(relative_pack_bias_V=.002))
    def test_discharge_sign_and_pack_not_cell_sum(self):
        self.assertGreater(np.median(self.t.pack_v-self.t.cell_v.sum(axis=1)), -0.01)
        self.assertLess(abs(np.median(self.t.pack_v-self.t.cell_v.sum(axis=1))),.01)
    def test_same_model_recovery_long_window(self):
        x,y=self.t.window(40,50,scale=.94,n=101)
        p=fit_profile(self.t,x,y,40,np.arange(.90,1.001,.01),[0], [0],.001)
        self.assertAlmostEqual(float(p.loc[p.data_mse_V2.idxmin(),'C_scale']),.94,places=6)

if __name__=='__main__':unittest.main()
