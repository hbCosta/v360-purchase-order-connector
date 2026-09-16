from decimal import Decimal

import pytest

from app.domain.enums import OrderStatus, SourceSystem
from app.domain.exceptions import AdapterParsingError
from app.integrations.beta.adapter import parse_orders

# CSVs de amostra do enunciado (requirements.md §9).
CABECALHO_CSV = (
    "NUMERO_PEDIDO;FORNECEDOR_CNPJ;FORNECEDOR_RAZAO_SOCIAL;EMISSAO;SITUACAO;MOEDA\n"
    "20260088412;12.345.678/0001-90;Distribuidora Horizonte Ltda;15/08/2026;EM ABERTO;BRL\n"
    "20260088413;98.765.432/0001-55;Frigorífico Boa Mesa S.A.;01/08/2026;BLOQUEADO;BRL\n"
)

ITENS_CSV = (
    "NUMERO_PEDIDO;ITEM;CODIGO_MATERIAL;DESCRICAO;UNIDADE;QTD_PEDIDA;QTD_RECEBIDA;PRECO_UNITARIO\n"
    "20260088412;1;MAT-77;Óleo de soja 900ml;UN;1.200,000;400,000;6,49\n"
    "20260088412;2;MAT-78;Açúcar refinado 1kg;UN;500,000;0,000;4,15\n"
    "20260088413;1;MAT-91;Carne bovina dianteiro kg;KG;2.000,000;0,000;27,90\n"
)


class TestParseOrders:
    def test_returns_one_order_per_header_row(self):
        orders = parse_orders(CABECALHO_CSV, ITENS_CSV)
        assert len(orders) == 2

    def test_items_grouped_by_numero_pedido(self):
        orders = {o.po_number: o for o in parse_orders(CABECALHO_CSV, ITENS_CSV)}
        assert len(orders["20260088412"].items) == 2
        assert len(orders["20260088413"].items) == 1

    def test_order_header_fields(self):
        orders = {o.po_number: o for o in parse_orders(CABECALHO_CSV, ITENS_CSV)}
        order = orders["20260088412"]
        assert order.source_system == SourceSystem.BETA
        assert order.created_at.isoformat() == "2026-08-15"
        assert order.status == OrderStatus.OPEN
        assert order.currency == "BRL"

    def test_vendor_tax_id_is_normalized(self):
        orders = {o.po_number: o for o in parse_orders(CABECALHO_CSV, ITENS_CSV)}
        assert orders["20260088412"].vendor.tax_id == "12345678000190"
        assert orders["20260088412"].vendor.name == "Distribuidora Horizonte Ltda"
        assert orders["20260088413"].vendor.tax_id == "98765432000155"

    def test_item_fields_and_pending_quantity(self):
        orders = {o.po_number: o for o in parse_orders(CABECALHO_CSV, ITENS_CSV)}
        item = orders["20260088412"].items[0]
        assert item.line == 1
        assert item.material == "MAT-77"
        assert item.uom == "UN"
        assert item.quantity_ordered == Decimal("1200.000")
        assert item.quantity_received == Decimal("400.000")
        assert item.unit_price == Decimal("6.49")
        assert item.quantity_pending == Decimal("800.000")

    def test_second_order_is_blocked_with_kg_item(self):
        orders = {o.po_number: o for o in parse_orders(CABECALHO_CSV, ITENS_CSV)}
        order = orders["20260088413"]
        assert order.status == OrderStatus.BLOCKED
        assert order.items[0].uom == "KG"
        assert order.items[0].quantity_pending == Decimal("2000.000")

    @pytest.mark.parametrize(
        ("raw_status", "expected"),
        [
            ("EM ABERTO", OrderStatus.OPEN),
            ("BLOQUEADO", OrderStatus.BLOCKED),
            ("ENCERRADO", OrderStatus.CLOSED),  # suposição S7
        ],
    )
    def test_status_mapping(self, raw_status: str, expected: OrderStatus):
        cabecalho = (
            "NUMERO_PEDIDO;FORNECEDOR_CNPJ;FORNECEDOR_RAZAO_SOCIAL;EMISSAO;SITUACAO;MOEDA\n"
            f"1;12.345.678/0001-90;Fornecedor X;01/01/2026;{raw_status};BRL\n"
        )
        orders = parse_orders(cabecalho, "NUMERO_PEDIDO;ITEM;CODIGO_MATERIAL;DESCRICAO;UNIDADE;QTD_PEDIDA;QTD_RECEBIDA;PRECO_UNITARIO\n")
        assert orders[0].status == expected

    def test_unknown_status_raises_adapter_parsing_error(self):
        cabecalho = (
            "NUMERO_PEDIDO;FORNECEDOR_CNPJ;FORNECEDOR_RAZAO_SOCIAL;EMISSAO;SITUACAO;MOEDA\n"
            "1;12.345.678/0001-90;Fornecedor X;01/01/2026;CANCELADO;BRL\n"
        )
        with pytest.raises(AdapterParsingError):
            parse_orders(cabecalho, "NUMERO_PEDIDO;ITEM;CODIGO_MATERIAL;DESCRICAO;UNIDADE;QTD_PEDIDA;QTD_RECEBIDA;PRECO_UNITARIO\n")

    def test_header_without_matching_items_yields_empty_items(self):
        cabecalho_extra = (
            CABECALHO_CSV
            + "99999999999;11.111.111/0001-11;Fornecedor Sem Itens;01/01/2026;EM ABERTO;BRL\n"
        )
        orders = {o.po_number: o for o in parse_orders(cabecalho_extra, ITENS_CSV)}
        assert orders["99999999999"].items == []

    def test_orphan_item_without_header_raises_adapter_parsing_error(self):
        itens_orfao = ITENS_CSV + "77777777777;1;MAT-1;Item orfao;UN;1,000;0,000;1,00\n"
        with pytest.raises(AdapterParsingError):
            parse_orders(CABECALHO_CSV, itens_orfao)
