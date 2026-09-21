from datetime import datetime, timezone
from decimal import Decimal
import pytest
from quant_research.execution import Kind, Order, OrderBook, Side, Status
from quant_research.risk import annualized_ratios, historical_var_es, max_drawdown, returns

NOW = datetime(2025,1,1,tzinfo=timezone.utc)
def order(i, side, qty, price): return Order(i, NOW, "SYN", side, qty, Kind.LIMIT, Decimal(price))

def test_price_time_priority_partial_fill_and_cost_conservation():
    book=OrderBook(); book.submit(order("s1",Side.SELL,2,"101")); book.submit(order("s2",Side.SELL,3,"102"))
    state, fills=book.submit(order("b",Side.BUY,4,"102"))
    assert [(x.sell_id,x.quantity,x.price) for x in fills] == [("s1",2,Decimal("101")),("s2",2,Decimal("102"))]
    assert state.status is Status.FILLED and book.orders["s2"].status is Status.PARTIAL
    assert sum(x.quantity*x.price for x in fills) == Decimal("406")

def test_order_edge_cases_and_cancel_guards():
    book=OrderBook(); rejected,_=book.submit(order("bad",Side.BUY,0,"1")); assert rejected.status is Status.REJECTED
    book.submit(order("a",Side.BUY,1,"9")); book.cancel("a")
    with pytest.raises(ValueError): book.cancel("a")
    with pytest.raises(ValueError, match="duplicate"): book.submit(order("a",Side.BUY,1,"9"))

def test_risk_metrics_and_warnings():
    eq=[100,110,88,92]; r=returns(eq)
    assert max_drawdown(eq) == pytest.approx(-.2)
    assert annualized_ratios(r)["warning"] == "tiny sample"
    var,es,warning=historical_var_es(r); assert es >= var and warning == "tiny sample"
