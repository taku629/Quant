import pytest
from quant_research.benchmark import measure
from quant_research.dashboard import render

def test_dashboard_e2e_contains_computed_values_and_accessible_chart():
    page=render(seed=5,periods=30)
    assert "Computed equity" in page and "aria-label='equity curve'" in page and "Simulation only" in page
    assert "<tbody><tr>" in page

def test_benchmark_is_bounded_and_reports_real_measurements():
    result=measure(symbols=2,periods=20,seed=1)
    assert result["events"]==40 and result["wall_seconds"]>0 and result["python_peak_bytes"]>0
    with pytest.raises(ValueError,match="bounds"): measure(periods=10001)
