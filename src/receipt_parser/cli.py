"""CLI парсера чеков."""

from __future__ import annotations

import argparse
import json
import sys

from .exceptions import ReceiptParseError
from .fiscal_parser import parse_fiscal_receipt
from .text_parser import parse_text_receipt


def _print_human(receipt) -> None:
    print(f"Магазин:   {receipt.store}")
    print(f"Дата:      {receipt.date}")
    print(f"Чек №:     {receipt.receipt_number}")
    print(f"ФН/ФД:     {receipt.fn_number} / {receipt.fd_number}")
    print("-" * 50)
    for it in receipt.items:
        print(f"{it.name:<30} {it.quantity:>6} x {it.unit_price:>8.2f} = {it.total:>9.2f}")
    print("-" * 50)
    print(f"По позициям: {receipt.calculate_total():.2f}")
    print(f"Итог:        {receipt.total}")
    print(f"Сходится:    {receipt.is_balanced()}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="receipt-parser",
        description="Парсер чеков: текстовый и бинарный фискальный (TLV/ККТ).",
    )
    parser.add_argument("path", help="Файл с чеком")
    parser.add_argument(
        "--format",
        choices=["text", "fiscal"],
        default="text",
        help="Формат входного файла (по умолчанию text)",
    )
    parser.add_argument("--json", action="store_true", help="Вывод в JSON")
    parser.add_argument(
        "--encoding", default="utf-8", help="Кодировка для текстовых тегов (fiscal)"
    )
    args = parser.parse_args(argv)

    mode = "rb" if args.format == "fiscal" else "r"
    try:
        with open(args.path, mode) as fh:
            data = fh.read()
        if args.format == "fiscal":
            receipt = parse_fiscal_receipt(data, encoding=args.encoding)
        else:
            receipt = parse_text_receipt(data)
    except FileNotFoundError:
        print(f"Файл не найден: {args.path}", file=sys.stderr)
        return 2
    except (ReceiptParseError, ValueError) as exc:
        print(f"Ошибка разбора: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(receipt.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_human(receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
