"""Research-only official adapter: R02 quality gate with frozen CK0 fallback.

R02 is not activated without qualified reference conditions and usable windows.
R05 has D1 proxy evidence only and cannot train a group prior from one group.
"""
class ResearchCandidate:
    def __init__(self):
        self.anchor_capacity_Ah=None
        self.nominal_capacity_Ah=102.0
        self.r02_capacity_update_qualified=False
        self.r05_group_prior_qualified=False
    def fit(self,dataset):
        released=dataset.checkups_released
        anchor=released.loc[released.checkup.eq('CK0'),'capacity_Ah']
        if len(anchor)!=1: raise ValueError('CK0 anchor missing or duplicated')
        self.anchor_capacity_Ah=float(anchor.iloc[0])
        if not (0<self.anchor_capacity_Ah<self.nominal_capacity_Ah*1.5):raise ValueError('invalid anchor')
        return self
    def estimate_soh(self,dataset,checkup_date):
        if self.anchor_capacity_Ah is None:raise RuntimeError('fit must run first')
        # The full operation supplied to fit is intentionally never persisted.
        return 100.0*self.anchor_capacity_Ah/self.nominal_capacity_Ah
