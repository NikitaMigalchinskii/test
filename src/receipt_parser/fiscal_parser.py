"""Разбор бинарного фискального TLV-формата чеков ККТ/ФН (54-ФЗ).

Чек фискального накопителя представляет из себя поток записей TLV:
``[тег: 2 байта LE][длина: 2 байта LE][значение: длина байт]``.

Значения числовых тегов закодированы как беззнаковое целое little-endian
в масштабе 1/100 (копейки). Строковые теги — CP1251/UTF-8.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Iterator, Optional

from .exceptions import ReceiptParseError
from .models import Item, Receipt

# Основные теги ФФД 1.05/1.1
TAG_FN = 1077          # номер фискального накопителя
TAG_FD = 1041          # номер документа (ФД)
TAG_RECEIPT_NO = 1040  # номер чека
TAG_STORE = 1039       # наименование организации
TAG_DATE = 1012        # дата/время (в текстовом виде)
TAG_ITEM_NAME = 1030   # наименование товара
TAG_ITEM_NAME_ALT = 1163
TAG_QTY = 1023         # количество
TAG_ITEM_TOTAL = 1020  # стоимость позиции
TAG_PRICE = 1019       # цена за единицу
TAG_TOTAL = 1059       # итоговая сумма
TAG_TAX = 1199         # сумма НДС


@dataclass
class TaggedRecord:
    """Одна TLV-запись."""

    tag: int
    length: int
    raw: bytes

    def as_int(self) -> int:
        return int.from_bytes(self.raw, "little", signed=False)

    def as_money(self) -> float:
        return self.as_int() / 100.0

    def as_text(self, encoding: str = "utf-8") -> str:
        for enc in (encoding, "cp1251", "latin-1"):
            try:
                return self.raw.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return self.raw.decode("latin-1", errors="replace")


def iter_records(data: bytes) -> Iterator[TaggedRecord]:
    """Итерировать TLV-записи из потока байтов."""
    offset = 0
    size = len(data)
    while offset + 4 <= size:
        tag, length = struct.unpack_from("<HH", data, offset)
        offset += 4
        if offset + length > size:
            raise ReceiptParseError(
                f"Обрезанная запись: тег {tag}, длина {length} за пределами данных"
            )
        yield TaggedRecord(tag=tag, length=length, raw=data[offset:offset + length])
        offset += length


def _first(records: list[TaggedRecord], tag: int) -> Optional[TaggedRecord]:
    for r in records:
        if r.tag == tag:
            return r
    return None


def parse_fiscal_receipt(data: bytes, encoding: str = "utf-8") -> Receipt:
    """Разобрать бинарный чек ККТ в :class:`Receipt`."""
    if not data:
        raise ReceiptParseError("Пустые данные чека")

    records = list(iter_records(data))
    receipt = Receipt()

    fn = _first(records, TAG_FN)
    if fn:
        receipt.fn_number = str(fn.as_int())
    fd = _first(records, TAG_FD)
    if fd:
        receipt.fd_number = str(fd.as_int())
    no = _first(records, TAG_RECEIPT_NO)
    if no:
        receipt.receipt_number = str(no.as_int())
    store = _first(records, TAG_STORE)
    if store:
        receipt.store = store.as_text(encoding)
    total = _first(records, TAG_TOTAL)
    if total:
        receipt.total = total.as_money()

    # Позиции: идём по потоку и группируем вокруг тега наименования.
    current: Optional[Item] = None
    for r in records:
        if r.tag in (TAG_ITEM_NAME, TAG_ITEM_NAME_ALT):
            if current is not None:
                receipt.items.append(current)
            current = Item(name=r.as_text(encoding))
        elif current is not None:
            if r.tag == TAG_QTY:
                current.quantity = r.as_money()
            elif r.tag == TAG_PRICE:
                current.unit_price = r.as_money()
            elif r.tag == TAG_ITEM_TOTAL:
                current.total = r.as_money()
    if current is not None:
        receipt.items.append(current)

    tax = _first(records, TAG_TAX)
    if tax:
        try:
            receipt.tax = tax.as_money()
        except Exception:
            pass
    return receipt
