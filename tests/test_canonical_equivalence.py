"""RF3.1 — Alfa e Beta devem produzir o mesmo modelo canônico para dados de negócio equivalentes.

Este teste não pertence a nenhum adapter específico: ele existe para provar, no nível do
domínio, que nenhuma lógica downstream precisa checar o cliente de origem (design.md, regra de
ouro §1).
"""

from datetime import date
from decimal import Decimal

from app.domain.enums import OrderStatus, SourceSystem
from app.integrations.alfa.adapter import parse_orders as parse_alfa_orders
from app.integrations.alfa.schemas import AlfaIngestionPayload
from app.integrations.beta.adapter import parse_orders as parse_beta_orders

# Mesmo pedido de negócio, descrito nos dois formatos: mesmo fornecedor (CNPJ com máscaras
# diferentes), mesma data, mesma situação (aberto), mesmo item com mesma quantidade e preço.

ALFA_PAYLOAD = {
    "purchase_orders": [
        {
            "po_number": "4500001234",
            "created_at": "2026-08-05",
            "status": "open",
            "currency": "BRL",
            "vendor": {"tax_id": "12345678000190", "name": "Fornecedor Teste Ltda"},
            "items": [
                {
                    "line": 1,
                    "material": "MAT-1",
                    "description": "Item Teste",
                    "uom": "UN",
                    "quantity_ordered": 100,
                    "quantity_received": 60,
                    "unit_price": 45.9,
                }
            ],
        }
    ]
}

BETA_CABECALHO_CSV = (
    "NUMERO_PEDIDO;FORNECEDOR_CNPJ;FORNECEDOR_RAZAO_SOCIAL;EMISSAO;SITUACAO;MOEDA\n"
    "20260099999;12.345.678/0001-90;Fornecedor Teste Ltda;05/08/2026;EM ABERTO;BRL\n"
)

BETA_ITENS_CSV = (
    "NUMERO_PEDIDO;ITEM;CODIGO_MATERIAL;DESCRICAO;UNIDADE;QTD_PEDIDA;QTD_RECEBIDA;PRECO_UNITARIO\n"
    "20260099999;1;MAT-1;Item Teste;UN;100,000;60,000;45,90\n"
)


def test_alfa_and_beta_produce_equivalent_canonical_orders():
    alfa_order = parse_alfa_orders(AlfaIngestionPayload.model_validate(ALFA_PAYLOAD))[0]
    beta_order = parse_beta_orders(BETA_CABECALHO_CSV, BETA_ITENS_CSV)[0]

    # As únicas diferenças esperadas são a identidade do pedido (RN3): fonte e número.
    assert alfa_order.source_system == SourceSystem.ALFA
    assert beta_order.source_system == SourceSystem.BETA
    assert alfa_order.po_number != beta_order.po_number

    # Todo o resto deve ser igual em tipo e valor.
    assert type(alfa_order.created_at) is type(beta_order.created_at) is date
    assert alfa_order.created_at == beta_order.created_at == date(2026, 8, 5)

    assert alfa_order.status == beta_order.status == OrderStatus.OPEN
    assert alfa_order.currency == beta_order.currency == "BRL"

    assert alfa_order.vendor.tax_id == beta_order.vendor.tax_id == "12345678000190"
    assert alfa_order.vendor.name == beta_order.vendor.name == "Fornecedor Teste Ltda"

    assert len(alfa_order.items) == len(beta_order.items) == 1
    alfa_item, beta_item = alfa_order.items[0], beta_order.items[0]

    assert alfa_item.line == beta_item.line == 1
    assert alfa_item.material == beta_item.material == "MAT-1"
    assert alfa_item.description == beta_item.description == "Item Teste"
    assert alfa_item.uom == beta_item.uom == "UN"

    for field in ("quantity_ordered", "quantity_received", "unit_price"):
        alfa_value = getattr(alfa_item, field)
        beta_value = getattr(beta_item, field)
        assert type(alfa_value) is type(beta_value) is Decimal
        assert alfa_value == beta_value

    assert alfa_item.quantity_ordered == beta_item.quantity_ordered == Decimal("100")
    assert alfa_item.quantity_received == beta_item.quantity_received == Decimal("60")
    assert alfa_item.unit_price == beta_item.unit_price == Decimal("45.9")
    assert alfa_item.quantity_pending == beta_item.quantity_pending == Decimal("40")
