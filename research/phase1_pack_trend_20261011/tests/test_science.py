import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/"src"))
from trend import feedback,summarize_trend,training_log_ratios
from pack import PackPrototype

def fragments(rate=.001, temperatures=None):
    rows=[]
    for i in range(6):
        d=10*i
        r=dict(fragment_end=(pd.Timestamp("2025-01-01")+pd.Timedelta(days=d)).isoformat(),
               temperature_C=25. if temperatures is None else temperatures[i],current_A=10.)
        r.update({f"w{j:02d}_Ah":(j+1)*np.exp(-rate*d) for j in range(9)})
        rows.append(r)
    return pd.DataFrame(rows)

def test_exponential_window_trend_is_signed_log_derivative():
    for rate in [.001,-.002]:
        tr=summarize_trend(fragments(rate),"2025-03-01")
        assert tr["median_slope_per_day"]==pytest.approx(rate,abs=1e-12)
        assert tr["valid_windows"]==9

def test_incompatible_temperature_does_not_create_aging_observation():
    tr=summarize_trend(fragments(temperatures=np.arange(6)*10.),"2025-03-01")
    assert not tr["eligible"]
    assert tr["valid_windows"]==0

def test_fragment_future_is_rejected():
    with pytest.raises(ValueError):summarize_trend(fragments(),"2025-01-10")

def test_capacity_labels_are_not_A_features():
    f=fragments();expected=summarize_trend(f,"2025-03-01")
    f["target_capacity_Ah"]=np.arange(6)*1e9
    f["full_charge_Ah"]=1e12
    assert summarize_trend(f,"2025-03-01")==expected

def test_forward_observation_changes_only_future_loss():
    pred,log=feedback([99.,98.,97.],100.,[np.log(2),0,0],[True,False,False],["a","a","a"],1.,"forward")
    assert pred.tolist()==pytest.approx([99.,97.,95.])
    assert log[0]["multiplier_used"]==1.
    assert log[0]["multiplier_next"]==2.

def test_event_dedup_and_quality_gate():
    pred,log=feedback([99.,98.,97.],100.,[np.log(2)]*3,[False,True,True],["a"]*3,.3,"forward")
    assert pred[0]==99 and pred[1]==98
    assert [z["accepted"] for z in log]==[False,True,False]
    assert log[2]["multiplier_next"]==pytest.approx(2**.3)

@pytest.mark.parametrize("mode",["forward","damage"])
def test_zero_gain_identity_and_prefix_equivalence(mode):
    b=np.array([99.,98.3,95.]);z=[10.,-10.,2.];q=[True]*3;e=["a","b","c"]
    output,_=feedback(b,100,z,q,e,0,mode)
    assert np.allclose(output,b,atol=1e-12)
    full,_=feedback(b,100,z,q,e,.3,mode)
    prefix,_=feedback(b[:2],100,z[:2],q[:2],e[:2],.3,mode)
    assert np.array_equal(full[:2],prefix)

def test_training_rate_labels_do_not_cross_entities():
    y=training_log_ratios([99,98,97,96],[98,96,94,92],100,"forward")
    assert y[:3]==pytest.approx(np.log(2))
    assert np.isnan(y[-1])

def make_pack():
    q=np.array([0.,5.,10.,15.,20.]);pack=np.array([13.,12.,11.,12.,10.])
    return PackPrototype(pd.DataFrame({"discharged_Ah":q,"voltage_V":pack,
        **{f"cell{i}_V":pack/4 for i in range(1,5)}}),q0=9.)

def test_first_crossing_not_later_root():
    p=make_pack()
    assert p.capacity(1)==pytest.approx(9.)
    assert p.capacity(.8)==pytest.approx(7.2)

def test_bounded_template_and_negative_soc_shift_rejected():
    p=make_pack()
    with pytest.raises(ValueError):p.capacity([.01,1,1,1])
    with pytest.raises(ValueError):p.capacity(1,[-1,0,0,0])

def test_pack_channel_permutation_is_identity():
    p=make_pack();s=np.array([.97,.98,.99,1.])
    first=p.capacity(s)
    # Same curves here, but general state/curve permutation must commute.
    p.v=p.v[:,[3,1,0,2]]
    assert p.capacity(s[[3,1,0,2]])==pytest.approx(first,abs=1e-10)

def test_bad_mode_and_vector_lengths_rejected():
    with pytest.raises(ValueError):feedback([99],100,[],[],[],.3,"forward")
    with pytest.raises(ValueError):feedback([99],100,[0],[True],["a"],.3,"unknown")

def test_event_coordinate_uses_registered_past_count():
    f=fragments(.001)
    f["event_ordinal"]=[1,11,21,31,41,51]
    tr=summarize_trend(f,"2025-03-01","events")
    assert tr["median_slope_per_event"]==pytest.approx(.001,abs=1e-12)
    with pytest.raises(ValueError):summarize_trend(f.drop(columns="event_ordinal"),"2025-03-01","events")
