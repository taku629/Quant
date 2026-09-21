"""Small immutable domain objects used by the simulator."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class Side(StrEnum):
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
    created_at: datetime
    symbol: str
    side: Side
    quantity: int


@dataclass(frozen=True, slots=True)
class Fill:
    order_id: int
    signal_at: datetime
    filled_at: datetime
    symbol: str
    side: Side
    quantity: int
    price: Decimal
    fee: Decimal
