import struct

import pytest

from receipt_parser import ReceiptParseError, parse_fiscal_receipt
from receipt_parser.fiscal_parser import iter_records

TAG_STORE = 1039
TAG_FN = 1077
TAG_FD = 1041
TAG_RECEIPT_NO = 1040
TAG_ITEM_NAME = 1030
TAG_QTY = 1023
TAG_PRICE = 1019
TAG_ITEM_TOTAL = 1020
TAG_TOTAL = 1059


def tlv(tag: int, raw: bytes) -> bytes:
    return struct.pack("<HH", tag, len(raw)) + raw


def money(value: float) -> bytes:
    return int(round(value * 100)).to_bytes(4, "little")


def build():
    data = b""
    data += tlv(TAG_STORE, "Магазин У Палыча".encode("utf-8"))
    data += tlv(TAG_FN, (9960440300212345).to_bytes(8, "little"))
    data += tlv(TAG_FD, (128765).to_bytes(4, "little"))
    data += tlv(TAG_RECEIPT_NO, (77).to_bytes(4, "little"))
    # позиция 1
    data += tlv(TAG_ITEM_NAME, "Кофе американо".encode("utf-8"))
    data += tlv(TAG_QTY, money(1))
    data += tlv(TAG_PRICE, money(120.0))
    data += tlv(TAG_ITEM_TOTAL, money(120.0))
    # позиция 2
    data += tlv(TAG_ITEM_NAME, "Круассан".encode("utf-8"))
    data += tlv(TAG_QTY, money(2))
    data += tlv(TAG_PRICE, money(65.5))
    data += tlv(TAG_ITEM_TOTAL, money(131.0))
    data += tlv(TAG_TOTAL, money(251.0))
    return data


def test_iter_records_roundtrip():
    recs = list(iter_records(build()))
    tags = [r.tag for r in recs]
    assert TAG_ITEM_NAME in tags
    assert TAG_TOTAL in tags


def test_parse_fiscal_fields():
    r = parse_fiscal_receipt(build())
    assert r.store == "Магазин У Палыча"
    assert r.fn_number == "9960440300212345"
    assert r.fd_number == "128765"
    assert r.receipt_number == "77"
    assert r.total == 251.0


def test_parse_fiscal_items():
    r = parse_fiscal_receipt(build())
    assert len(r.items) == 2
    assert r.items[0].name == "Кофе американо"
    assert r.items[0].unit_price == 120.0
    assert r.items[1].quantity == 2.0
    assert r.items[1].total == 131.0
    assert r.calculate_total() == 251.0
    assert r.is_balanced() is True


def test_truncated_raises():
    data = build()
    with pytest.raises(ReceiptParseError):
        list(iter_records(data[:-1]))


def test_empty_raises():
    with pytest.raises(ReceiptParseError):
        parse_fiscal_receipt(b"")
