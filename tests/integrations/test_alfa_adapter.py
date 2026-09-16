from decimal import Decimal

import pytest

from app.domain.enums import OrderStatus, SourceSystem
from app.domain.exceptions import AdapterParsingError
from app.integrations.alfa.adapter import parse_orders
from app.integrations.alfa.schemas import AlfaIngestionPayload

# Payload de amostra do enunciado (requirements.md §9).
ALFA_SAMPLE_PAYLOAD = {
    "purchase_orders": [
        {
            "po_number": "4500001234",
            "created_at": "2026-08-05",
            "status": "open",
            "currency": "BRL",
            "vendor": {"tax_id": "23456789000101", "name": "Metalúrgica São Jorge S.A."},
            "items": [
                {
                    "line": 10,
                    "material": "MAT-1001",
                    "description": "Chapa de aço 2mm",
                    "uom": "UN",
                    "quantity_ordered": 100,
                    "quantity_received": 60,
                    "unit_price": 45.9,
                },
                {
                    "line": 20,
                    "material": "MAT-1002",
                    "description": "Perfil U 3m",
                    "uom": "UN",
                    "quantity_ordered": 50,
                    "quantity_received": 0,
                    "unit_price": 128.75,
                },
            ],
        }
    ]
}


def _parse(raw: dict) -> list:
    return parse_orders(AlfaIngestionPayload.model_validate(raw))


class TestParseOrders:
    def test_returns_one_order_per_purchase_order(self):
        orders = _parse(ALFA_SAMPLE_PAYLOAD)
        assert len(orders) == 1

    def test_order_header_fields(self):
        order = _parse(ALFA_SAMPLE_PAYLOAD)[0]
        assert order.source_system == SourceSystem.ALFA
        assert order.po_number == "4500001234"
        assert order.created_at.isoformat() == "2026-08-05"
        assert order.status == OrderStatus.OPEN
        assert order.currency == "BRL"

    def test_vendor_fields(self):
        order = _parse(ALFA_SAMPLE_PAYLOAD)[0]
        assert order.vendor.tax_id == "23456789000101"
        assert order.vendor.name == "Metalúrgica São Jorge S.A."

    def test_item_fields_and_pending_quantity(self):
        order = _parse(ALFA_SAMPLE_PAYLOAD)[0]
        assert len(order.items) == 2

        item0 = order.items[0]
        assert item0.line == 10
        assert item0.material == "MAT-1001"
        assert item0.uom == "UN"
        assert item0.quantity_ordered == Decimal("100")
        assert item0.quantity_received == Decimal("60")
        assert item0.unit_price == Decimal("45.9")
        assert item0.quantity_pending == Decimal("40")

        item1 = order.items[1]
        assert item1.quantity_received == Decimal("0")
        assert item1.quantity_pending == Decimal("50")

    @pytest.mark.parametrize(
        ("raw_status", "expected"),
        [("open", OrderStatus.OPEN), ("closed", OrderStatus.CLOSED), ("blocked", OrderStatus.BLOCKED)],
    )
    def test_status_mapping(self, raw_status: str, expected: OrderStatus):
        payload = {
            "purchase_orders": [{**ALFA_SAMPLE_PAYLOAD["purchase_orders"][0], "status": raw_status}]
        }
        order = _parse(payload)[0]
        assert order.status == expected

    def test_unknown_status_raises_adapter_parsing_error(self):
        payload = {
            "purchase_orders": [{**ALFA_SAMPLE_PAYLOAD["purchase_orders"][0], "status": "cancelled"}]
        }
        with pytest.raises(AdapterParsingError):
            _parse(payload)
