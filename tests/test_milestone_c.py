from datetime import datetime, timedelta, timezone
import pytest
from quant_research.data import synthetic_bars
from quant_research.engine import MeanReversion
from quant_research.research import block_bootstrap_mean, chronological_split, dataset_hash, walk_forward

def test_split_has_strict_boundaries_and_rejects_contamination():
    bars=synthetic_bars(periods=10); split=chronological_split(bars)
    assert split.train[-1].timestamp < split.validation[0].timestamp < split.test[0].timestamp
    with pytest.raises(ValueError,match="chronological"): chronological_split(list(reversed(bars)))

def test_walk_forward_never_trains_on_future():
    dates=[datetime(2024,1,1,tzinfo=timezone.utc)+timedelta(days=i) for i in range(12)]
    windows=list(walk_forward(dates,6,2))
    assert len(windows)==3 and all(train[-1] < test[0] for train,test in windows)
    assert len(windows[-1][0])==10

def test_bootstrap_and_hash_are_reproducible():
    values=[-.1,.2,.03,-.01,.05]*5
    assert block_bootstrap_mean(values,seed=9)==block_bootstrap_mean(values,seed=9)
    assert dataset_hash(synthetic_bars(periods=4))==dataset_hash(synthetic_bars(periods=4))

def test_mean_reversion_uses_only_supplied_history():
    bars=synthetic_bars(periods=8)
    strategy=MeanReversion(lookback=3)
    before=strategy.target(tuple(bars[:5])); changed=list(bars); changed[-1]=synthetic_bars(periods=1,seed=99)[0]
    assert strategy.target(tuple(changed[:5]))==before
