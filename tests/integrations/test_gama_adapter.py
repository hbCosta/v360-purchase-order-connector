from datetime import date
from decimal import Decimal

import pytest

from app.domain.enums import OrderStatus, SourceSystem
from app.domain.exceptions import AdapterParsingError
from app.integrations.gama.adapter import parse_orders
from app.integrations.gama.schemas import GamaItemRow

# Amostra do enunciado (requirements.md §9): GL-778 tem 2 itens em CX, GL-779 tem 1 item já em UN.
GAMA_SAMPLE_RAW = [
    {
        "ped": "GL-778",
        "item": 1,
        "cnpj_fornecedor": "34567890000112",
        "nome_fornecedor": "Transportes Ideal ME",
        "dt_criacao": 1786752000,
        "cod_mat": "TRP-01",
        "desc_mat": "Pallet de madeira",
        "um": "CX",
        "fator_conv": 12,
        "qtd_ped": 10,
        "qtd_rec": 2,
        "preco_unit_centavos": 120000,
        "situacao": 1,
    },
    {
        "ped": "GL-778",
        "item": 2,
        "cnpj_fornecedor": "34567890000112",
        "nome_fornecedor": "Transportes Ideal ME",
        "dt_criacao": 1786752000,
        "cod_mat": "TRP-09",
        "desc_mat": "Caixa organizadora",
        "um": "CX",
        "fator_conv": 3,
        "qtd_ped": 4,
        "qtd_rec": 0,
        "preco_unit_centavos": 10000,
        "situacao": 1,
    },
    {
        "ped": "GL-779",
        "item": 1,
        "cnpj_fornecedor": "56789012000134",
        "nome_fornecedor": "Armazéns Rio Claro Ltda",
        "dt_criacao": 1784160000,
        "cod_mat": "ARM-10",
        "desc_mat": "Estrado metálico",
        "um": "UN",
        "fator_conv": 1,
        "qtd_ped": 100,
        "qtd_rec": 100,
        "preco_unit_centavos": 3500,
        "situacao": 2,
    },
]


def _parse(raw: list[dict]) -> list:
    return parse_orders([GamaItemRow.model_validate(row) for row in raw])


class TestParseOrders:
    def test_groups_rows_into_two_orders(self):
        orders = _parse(GAMA_SAMPLE_RAW)
        assert len(orders) == 2
        assert {o.po_number for o in orders} == {"GL-778", "GL-779"}

    def test_gl778_has_two_items_from_first_row_header(self):
        orders = {o.po_number: o for o in _parse(GAMA_SAMPLE_RAW)}
        order = orders["GL-778"]
        assert order.source_system == SourceSystem.GAMA
        assert order.created_at == date(2026, 8, 15)
        assert order.status == OrderStatus.OPEN
        assert order.currency == "BRL"
        assert order.vendor.tax_id == "34567890000112"
        assert order.vendor.name == "Transportes Ideal ME"
        assert len(order.items) == 2

    def test_gl779_header_and_status_closed(self):
        orders = {o.po_number: o for o in _parse(GAMA_SAMPLE_RAW)}
        order = orders["GL-779"]
        assert order.created_at == date(2026, 7, 16)
        assert order.status == OrderStatus.CLOSED
        assert len(order.items) == 1


class TestUnitConversion:
    def test_cx_with_exact_division_converts_quantity_and_price(self):
        orders = {o.po_number: o for o in _parse(GAMA_SAMPLE_RAW)}
        item = orders["GL-778"].items[0]  # TRP-01: 10 CX, fator_conv=12
        assert item.uom == "UN"
        assert item.quantity_ordered == Decimal("120")
        assert item.quantity_received == Decimal("24")
        assert item.unit_price == Decimal("100")
        # valor total da linha preservado: 10 CX * R$1200,00 = 120 UN * R$100,00
        assert item.quantity_ordered * item.unit_price == Decimal("12000.00")

    def test_cx_with_non_exact_division_preserves_total_value(self):
        orders = {o.po_number: o for o in _parse(GAMA_SAMPLE_RAW)}
        item = orders["GL-778"].items[1]  # TRP-09: 4 CX, fator_conv=3
        assert item.uom == "UN"
        assert item.quantity_ordered == Decimal("12")
        # 100.00 / 3 não é exato — não deve ser pré-arredondado (ver T42)
        total = item.quantity_ordered * item.unit_price
        assert abs(total - Decimal("400.00")) < Decimal("0.0000000001")

    def test_item_already_in_un_passes_through_unchanged(self):
        orders = {o.po_number: o for o in _parse(GAMA_SAMPLE_RAW)}
        item = orders["GL-779"].items[0]  # ARM-10: já em UN, fator_conv=1
        assert item.uom == "UN"
        assert item.quantity_ordered == Decimal("100")
        assert item.quantity_received == Decimal("100")
        assert item.unit_price == Decimal("35.00")


class TestStatusMapping:
    @pytest.mark.parametrize(
        ("situacao", "expected"),
        [(1, OrderStatus.OPEN), (2, OrderStatus.CLOSED), (3, OrderStatus.BLOCKED)],
    )
    def test_known_situacao_codes(self, situacao: int, expected: OrderStatus):
        raw = [{**GAMA_SAMPLE_RAW[2], "situacao": situacao}]
        order = _parse(raw)[0]
        assert order.status == expected

    def test_unknown_situacao_raises_adapter_parsing_error(self):
        raw = [{**GAMA_SAMPLE_RAW[2], "situacao": 9}]
        with pytest.raises(AdapterParsingError):
            _parse(raw)
