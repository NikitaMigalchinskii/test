import struct

import pytest

from receipt_parser import (
    Item,
    Receipt,
    ReceiptParseError,
    parse_text_receipt,
)

SAMPLE = """МАГАЗИН: Пятёрочка
Дата: 10.09.2026 14:32:11
ЧЕК № 4213
ФН: 9960440300212345
ФД: 128765

Молоко 3.2% 950мл        2 x 89,99      179,98
Хлеб белый              1 x 45,50        45,50
Сыр Российский 200г     0,350 x 499,00  174,65
Сахар-песок 1кг         1 x 78,90        78,90
Жвачка Orbit            3 x 25,00        75,00

СУММА: 554,03
НДС 20%: 92,34
ИТОГО: 554,03
"""


def test_parse_store_and_meta():
    r = parse_text_receipt(SAMPLE)
    assert r.store == "МАГАЗИН: Пятёрочка" or "Пятёрочка" in (r.store or "")
    assert r.date == "10.09.2026 14:32:11"
    assert r.receipt_number == "4213"
    assert r.fn_number == "9960440300212345"
    assert r.fd_number == "128765"


def test_parse_items_count_and_values():
    r = parse_text_receipt(SAMPLE)
    assert len(r.items) == 5
    assert r.items[0].name == "Молоко 3.2% 950мл"
    assert r.items[0].quantity == 2
    assert r.items[0].unit_price == 89.99
    assert r.items[0].total == 179.98
    # дробное количество
    assert r.items[2].quantity == 0.350
    assert r.items[2].total == 174.65


def test_parse_totals_and_balance():
    r = parse_text_receipt(SAMPLE)
    assert r.total == 554.03
    assert r.tax == 92.34
    assert r.subtotal == 554.03
    assert r.calculate_total() == 554.03
    assert r.is_balanced() is True


def test_empty_input_raises():
    with pytest.raises(ReceiptParseError):
        parse_text_receipt("   \n  ")


def test_item_auto_total():
    it = Item(name="тест", quantity=3, unit_price=10.0)
    assert it.total == 30.0


def test_receipt_to_dict():
    r = Receipt(store="S", total=100.0, items=[Item("a", 1, 100.0, 100.0)])
    d = r.to_dict()
    assert d["store"] == "S"
    assert d["items"][0]["name"] == "a"
