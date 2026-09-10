"""Парсер чеков: текстовый и бинарный фискальный (TLV/ККТ) форматы."""

from .models import Item, Receipt
from .exceptions import ReceiptParseError
from .text_parser import parse_text_receipt
from .fiscal_parser import parse_fiscal_receipt, TaggedRecord

__all__ = [
    "Item",
    "Receipt",
    "ReceiptParseError",
    "parse_text_receipt",
    "parse_fiscal_receipt",
    "TaggedRecord",
]

__version__ = "0.1.0"
