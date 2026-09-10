"""Модели данных чека."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Item:
    """Позиция чека."""

    name: str
    quantity: float = 1.0
    unit_price: float = 0.0
    total: float = 0.0

    def __post_init__(self) -> None:
        if self.total == 0.0 and self.quantity and self.unit_price:
            self.total = round(self.quantity * self.unit_price, 2)


@dataclass
class Receipt:
    """Разобранный чек."""

    store: Optional[str] = None
    date: Optional[str] = None
    receipt_number: Optional[str] = None
    fn_number: Optional[str] = None
    fd_number: Optional[str] = None
    items: list = field(default_factory=list)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    raw: str = ""

    def calculate_total(self) -> float:
        """Сумма по позициям."""
        return round(sum(item.total for item in self.items), 2)

    def is_balanced(self, tolerance: float = 0.01) -> bool:
        """Сходится ли сумма позиций с итогом."""
        if self.total is None:
            return False
        return abs(self.calculate_total() - self.total) <= tolerance

    def to_dict(self) -> dict:
        return {
            "store": self.store,
            "date": self.date,
            "receipt_number": self.receipt_number,
            "fn_number": self.fn_number,
            "fd_number": self.fd_number,
            "items": [
                {
                    "name": i.name,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                    "total": i.total,
                }
                for i in self.items
            ],
            "subtotal": self.subtotal,
            "tax": self.tax,
            "total": self.total,
        }
