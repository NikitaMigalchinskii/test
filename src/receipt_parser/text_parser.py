"""Разбор текстового представления чека (эвристический)."""

from __future__ import annotations

import re

from .exceptions import ReceiptParseError
from .models import Item, Receipt

# Разделитель тысяч может быть пробелом, число может содержать дробь.
_MONEY = r"\d+(?:[ .]\d{3})*(?:[.,]\d{1,2})?"
# Позиция: "Название   2 x 89.99   179.98" или "Название   179.98"
_LINE_WITH_QTY = re.compile(
    rf"^(?P<name>.+?)\s+(?P<qty>\d+(?:[.,]\d+)?)\s*[xх*]\s*"
    rf"(?P<price>{_MONEY})\s+(?P<total>{_MONEY})\.?$"
)
_LINE_WITH_TOTAL = re.compile(rf"^(?P<name>\D.*?)\s+(?P<total>{_MONEY})\.?$")

_RE_TOTAL = re.compile(rf"^ИТОГО[:\s]+(?P<v>{_MONEY})")
_RE_SUBTOTAL = re.compile(rf"^(?:СУММА|СТОИМОСТЬ)[:\s]+(?P<v>{_MONEY})")
_RE_TAX_PREFIX = re.compile(r"^(?:НДС|Налог)")
_RE_STORE = re.compile(r"^(?:МАГАЗИН|Адрес)[\s:]+(?P<v>.+)$", re.IGNORECASE)
_RE_DATE = re.compile(
    r"(?P<v>\d{2}[./]\d{2}[./]\d{2,4}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?)"
)
_RE_RECEIPT_NO = re.compile(r"ЧЕК\s*№?\s*(?P<v>[\w-]+)", re.IGNORECASE)
_RE_FN = re.compile(r"ФН\s*:?\s*(?P<v>\d+)", re.IGNORECASE)
_RE_FD = re.compile(r"ФД\s*:?\s*(?P<v>\d+)", re.IGNORECASE)


def _to_float(value: str) -> float:
    """'1 234,56' -> 1234.56"""
    cleaned = value.replace(" ", "").replace("\u00a0", "")
    # последняя запятая/точка — десятичный разделитель
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    else:
        cleaned = cleaned.replace(",", ".")
    # убрать групповые разделители-точки, если дробной части нет
    if "," not in value and cleaned.count(".") > 1:
        cleaned = cleaned.replace(".", "")
    return float(cleaned)


def parse_text_receipt(text: str) -> Receipt:
    """Разобрать текстовый чек в модель :class:`Receipt`."""
    if not text or not text.strip():
        raise ReceiptParseError("Пустой ввод")

    receipt = Receipt(raw=text)
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or set(line) <= set("-="):
            continue

        m = _RE_TOTAL.match(line)
        if m:
            receipt.total = _to_float(m.group("v"))
            continue
        m = _RE_SUBTOTAL.match(line)
        if m:
            receipt.subtotal = _to_float(m.group("v"))
            continue
        if _RE_TAX_PREFIX.match(line):
            # убрать ставку вида "20%", чтобы не спутать её с суммой
            stripped = re.sub(r"\d+(?:[.,]\d+)?\s*%", " ", line)
            found = re.findall(_MONEY, stripped)
            if found:
                receipt.tax = _to_float(found[-1])
            continue
        m = _RE_FD.search(line)
        if m:
            receipt.fd_number = m.group("v")
            continue
        m = _RE_FN.search(line)
        if m:
            receipt.fn_number = m.group("v")
            continue
        m = _RE_RECEIPT_NO.search(line)
        if m:
            receipt.receipt_number = m.group("v")
            continue
        m = _RE_DATE.search(line)
        if m and ("дата" in line.lower() or "date" in line.lower()):
            receipt.date = m.group("v")
            continue
        m = _RE_STORE.match(line)
        if m and receipt.store is None:
            receipt.store = m.group("v")
            continue

        m = _LINE_WITH_QTY.match(line)
        if m:
            receipt.items.append(
                Item(
                    name=m.group("name").strip(),
                    quantity=_to_float(m.group("qty")),
                    unit_price=_to_float(m.group("price")),
                    total=_to_float(m.group("total")),
                )
            )
            continue
        # Не является позицией: если это первая непустая строка — считаем магазином.
        if not receipt.items and receipt.store is None and receipt.date is None:
            receipt.store = line
    return receipt
