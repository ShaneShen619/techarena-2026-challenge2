"""Your model. Implement fit() and estimate_soh(); keep the two signatures.

Everything your model may use is in the Dataset object (framework/data.py):
  dataset.operation           operating rows (10-s) up to the evaluation date
  dataset.checkups_released   the released checkup (CK0 only: 100.41 Ah = 98.44 % SOH of 102 Ah)
  dataset.reference_discharge beginning-of-life C/20 discharge curve
  dataset.eval_points         all checkup dates (for your own validation only)
The evaluation calls estimate_soh() once per hidden checkup, each time with the data cut at
that checkup's date. Return SOH in percent of the NOMINAL capacity (102 Ah): CK0 = 100.41 Ah = 98.44 %."""
import pandas as pd


class MyModel:
    def __init__(self):
        pass

    def fit(self, dataset):
        """Train on the released data (whole campaign operation data + checkup CK0).
        Pre-trained artefacts from open-source data may be shipped inside my_model/ and
        loaded here - the evaluation does not re-run your open-data pre-training."""
        raise NotImplementedError

    def estimate_soh(self, dataset, at_date) -> float:
        """SOH (% of the nominal 102 Ah) of the pack at `at_date`, using only `dataset` (causal cut)."""
        raise NotImplementedError
