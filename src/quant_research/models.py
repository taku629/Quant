from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True, slots=True)
class Bar:
    timestamp: datetime
    symbol: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


@dataclass(frozen=True, slots=True)
class Order:
    order_id: int
    symbol: str
    side: Side
    quantity: int
    submitted_at: datetime


@dataclass(frozen=True, slots=True)
class Fill:
    order_id: int
    symbol: str
    side: Side
    quantity: int
    signal_at: datetime
    filled_at: datetime
    price: Decimal
    fee: Decimal


@dataclass(frozen=True, slots=True)
class EquityPoint:
    timestamp: datetime
    cash: Decimal
    holdings: Decimal
    equity: Decimal
