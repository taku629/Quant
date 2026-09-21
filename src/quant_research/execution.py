"""Deterministic synthetic matching; this is not inferred from OHLCV."""
from __future__ import annotations
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import Enum
import itertools


class Side(str, Enum): BUY = "buy"; SELL = "sell"
class Kind(str, Enum): MARKET = "market"; LIMIT = "limit"
class Status(str, Enum): PENDING = "pending"; ACCEPTED = "accepted"; PARTIAL = "partially_filled"; FILLED = "filled"; CANCELED = "canceled"; REJECTED = "rejected"

@dataclass(frozen=True)
class Order:
    id: str; timestamp: datetime; symbol: str; side: Side; quantity: int
    kind: Kind = Kind.LIMIT; limit_price: Decimal | None = None
    status: Status = Status.PENDING; filled: int = 0

@dataclass(frozen=True)
class Match:
    buy_id: str; sell_id: str; quantity: int; price: Decimal

class OrderBook:
    """Price-time-priority book with explicit submitted synthetic liquidity."""
    def __init__(self) -> None:
        self.orders: dict[str, Order] = {}; self._seq: dict[str, int] = {}; self._counter = itertools.count()

    def submit(self, order: Order) -> tuple[Order, tuple[Match, ...]]:
        if order.id in self.orders: raise ValueError("duplicate order id")
        if order.quantity <= 0 or not order.symbol or (order.kind is Kind.LIMIT and (order.limit_price is None or order.limit_price <= 0)):
            rejected = replace(order, status=Status.REJECTED); self.orders[order.id] = rejected; return rejected, ()
        if order.kind is Kind.MARKET and order.limit_price is not None: raise ValueError("market orders cannot have a limit")
        self.orders[order.id] = replace(order, status=Status.ACCEPTED); self._seq[order.id] = next(self._counter)
        matches: list[Match] = []
        while self.orders[order.id].filled < order.quantity:
            active = self.orders[order.id]
            candidates = [x for x in self.orders.values() if x.symbol == order.symbol and x.side != order.side and x.status in (Status.ACCEPTED, Status.PARTIAL)]
            if active.kind is Kind.LIMIT:
                candidates = [x for x in candidates if x.kind is Kind.MARKET or (x.limit_price is not None and (x.limit_price <= active.limit_price if active.side is Side.BUY else x.limit_price >= active.limit_price))]
            if not candidates: break
            candidates.sort(key=lambda x: ((x.limit_price or (Decimal("Infinity") if x.side is Side.SELL else Decimal("-Infinity"))) * (1 if active.side is Side.BUY else -1), self._seq[x.id]))
            resting = candidates[0]
            price = resting.limit_price or active.limit_price
            if price is None: break  # two unpriced market orders cannot defensibly match
            qty = min(active.quantity-active.filled, resting.quantity-resting.filled)
            buy, sell = (active, resting) if active.side is Side.BUY else (resting, active)
            matches.append(Match(buy.id, sell.id, qty, price))
            for item in (active, resting):
                filled = item.filled + qty
                self.orders[item.id] = replace(item, filled=filled, status=Status.FILLED if filled == item.quantity else Status.PARTIAL)
        return self.orders[order.id], tuple(matches)

    def cancel(self, order_id: str) -> Order:
        order = self.orders[order_id]
        if order.status not in (Status.ACCEPTED, Status.PARTIAL): raise ValueError("order is not cancelable")
        self.orders[order_id] = replace(order, status=Status.CANCELED); return self.orders[order_id]
