import sys
import unittest
from pathlib import Path
import pandas as pd

T=Path(__file__).resolve().parents[1]
ROOT=T.parents[1]
sys.path.insert(0,str(T/'src'))
from rpt import extract_reference_capacity

P={'series_count':4,'nominal_Ah':102,'reference_current_A':5.1,'cutoff_pack_V':11.2,'full_charge_confirmed':True}

class TestRPT(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.raw=pd.read_csv(ROOT/'data/checkups/CK0_reference_discharge.csv.gz')
 def test_real_ck0_reintegrates_with_rounding_tolerance(self):
  x=extract_reference_capacity(self.raw,P)
  self.assertEqual(x.status,'accepted')
  self.assertAlmostEqual(x.capacity_Ah,100.412,delta=0.002)
  self.assertEqual(x.cutoff_index,70874)
 def test_partial_curve_is_not_capacity(self):
  x=extract_reference_capacity(self.raw.iloc[:1000],P)
  self.assertEqual(x.status,'rejected')
  self.assertEqual(x.reason,'cutoff_not_reached')
 def test_protocol_and_gap_fail_closed(self):
  self.assertEqual(extract_reference_capacity(self.raw,{**P,'series_count':1}).status,'rejected')
  d=self.raw.copy();d.loc[2000:,'timestamp']=(pd.to_datetime(d.loc[2000:,'timestamp'])+pd.Timedelta(seconds=60)).astype(str)
  x=extract_reference_capacity(d,P)
  self.assertEqual(x.reason,'unrecorded_gap_over_10s')

if __name__=='__main__':unittest.main()
