# receipt-parser

Парсер чеков на Python. Поддерживает два формата:

1. Текстовое представление чека (эвристический разбор).
2. Бинарный фискальный TLV-формат чеков ККТ/ФН (54-ФЗ, ФФД 1.05/1.1).

## Установка

```bash
pip install -e .
# для тестов
pip install -e ".[dev]"
```

## Использование как библиотека

```python
from receipt_parser import parse_text_receipt, parse_fiscal_receipt

# текстовый чек
receipt = parse_text_receipt(open("samples/receipt.txt").read())
print(receipt.store, receipt.total)
for item in receipt.items:
    print(item.name, item.quantity, item.unit_price, item.total)
print("Сходится:", receipt.is_balanced())

# бинарный фискальный чек (TLV)
with open("check.bin", "rb") as fh:
    receipt = parse_fiscal_receipt(fh.read())
```

## CLI

```bash
# человекочитаемый вывод текстового чека
receipt-parser samples/receipt.txt

# JSON
receipt-parser samples/receipt.txt --json

# бинарный фискальный чек
receipt-parser check.bin --format fiscal --encoding cp1251
```

## Структура

```
src/receipt_parser/
  models.py        # Item, Receipt
  text_parser.py   # parse_text_receipt
  fiscal_parser.py # parse_fiscal_receipt, iter_records (TLV)
  exceptions.py    # ReceiptParseError
  cli.py           # CLI
tests/             # pytest-тесты
samples/           # пример текстового чека
```

## Формат TLV (fiscal)

Поток записей: `[тег: 2 байта LE][длина: 2 байта LE][значение]`.
Числовые теги — беззнаковое целое little-endian в масштабе 1/100.
Основные теги: 1039 магазин, 1030 наименование, 1023 количество,
1019 цена, 1020 стоимость, 1059 итог, 1077 ФН, 1041 ФД.

## Тесты

```bash
python -m pytest -q
```
