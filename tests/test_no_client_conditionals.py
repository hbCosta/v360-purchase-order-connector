"""T45 — A Parte 2 (Gama) não deve introduzir código condicional por cliente nas regras centrais.

RNF3: "Nenhuma lógica de negócio ou de API deve conter condicionais por cliente de origem
(`if source_system == "alfa"`); essas particularidades ficam restritas aos adapters."

Duas garantias, uma estrutural e uma funcional:
1. Os módulos de `services/` nunca referenciam um membro específico do enum `SourceSystem`
   (`SourceSystem.ALFA`/`BETA`/`GAMA`) — só o tipo, como parâmetro de filtro.
2. Uma conferência contra um pedido do Gama passa pelo mesmo `invoice_check_service.check()`
   usado por Alfa/Beta, produzindo os mesmos tipos de divergência.
"""

import inspect
from decimal import Decimal

from app.domain.enums import CheckStatus, DivergenceType, SourceSystem
from app.domain.invoice import Invoice, InvoiceItem
from app.domain.models import Vendor
from app.integrations.gama.adapter import parse_orders as parse_gama_orders
from app.integrations.gama.schemas import GamaItemRow
from app.services import invoice_check_service, purchase_order_service, report_service
from app.services.invoice_check_service import check

_CLIENT_SPECIFIC_TOKENS = (
    "SourceSystem.ALFA",
    "SourceSystem.BETA",
    "SourceSystem.GAMA",
)


class TestNoClientConditionalsInCoreServices:
    def test_invoice_check_service_has_no_client_specific_branch(self):
        source = inspect.getsource(invoice_check_service)
        for token in _CLIENT_SPECIFIC_TOKENS:
            assert token not in source, f"{token} não deveria aparecer em invoice_check_service"

    def test_purchase_order_service_has_no_client_specific_branch(self):
        source = inspect.getsource(purchase_order_service)
        for token in _CLIENT_SPECIFIC_TOKENS:
            assert token not in source, f"{token} não deveria aparecer em purchase_order_service"

    def test_report_service_has_no_client_specific_branch(self):
        source = inspect.getsource(report_service)
        for token in _CLIENT_SPECIFIC_TOKENS:
            assert token not in source, f"{token} não deveria aparecer em report_service"


GAMA_RAW_ITEM = {
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
}


def _gama_order():
    return parse_gama_orders([GamaItemRow.model_validate(GAMA_RAW_ITEM)])[0]


class TestInvoiceCheckServiceWorksIdenticallyForGama:
    def test_compliant_invoice_against_gama_order(self):
        order = _gama_order()  # já convertido: 120 UN a R$100,00
        invoice = Invoice(
            source_system=SourceSystem.GAMA,
            po_number="GL-778",
            vendor=Vendor(tax_id="34567890000112", name="Transportes Ideal ME"),
            items=[InvoiceItem(material="TRP-01", quantity=Decimal("96"), total_value=Decimal("9600.00"))],
        )
        result = check(order, invoice)
        assert result.status == CheckStatus.COMPLIANT
        assert result.discrepancies == []

    def test_divergent_invoice_against_gama_order_same_discrepancy_types(self):
        order = _gama_order()
        invoice = Invoice(
            source_system=SourceSystem.GAMA,
            po_number="GL-778",
            vendor=Vendor(tax_id="99999999000199", name="Outro"),  # fornecedor errado
            items=[InvoiceItem(material="TRP-01", quantity=Decimal("999"), total_value=Decimal("1.00"))],
        )
        result = check(order, invoice)
        types = {d.type for d in result.discrepancies}
        assert result.status == CheckStatus.DIVERGENT
        assert DivergenceType.VENDOR_MISMATCH in types
        assert DivergenceType.QUANTITY_EXCEEDS_PENDING in types
        assert DivergenceType.PRICE_MISMATCH in types
