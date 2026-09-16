from datetime import date
from decimal import Decimal

import pytest

from app.domain.enums import CheckStatus, DivergenceType, OrderStatus, SourceSystem
from app.domain.invoice import Invoice, InvoiceItem
from app.domain.models import PurchaseOrder, PurchaseOrderItem, Vendor
from app.services.invoice_check_service import check

ORDER_VENDOR_TAX_ID = "23456789000101"


@pytest.fixture
def order() -> PurchaseOrder:
    return PurchaseOrder(
        source_system=SourceSystem.ALFA,
        po_number="4500001234",
        created_at=date(2026, 8, 5),
        status=OrderStatus.OPEN,
        currency="BRL",
        vendor=Vendor(tax_id=ORDER_VENDOR_TAX_ID, name="Metalúrgica São Jorge S.A."),
        items=[
            PurchaseOrderItem(
                line=10,
                material="MAT-1001",
                description="Chapa de aço 2mm",
                uom="UN",
                quantity_ordered=Decimal("100"),
                quantity_received=Decimal("60"),
                unit_price=Decimal("45.9"),
            ),
            PurchaseOrderItem(
                line=20,
                material="MAT-1002",
                description="Perfil U 3m",
                uom="UN",
                quantity_ordered=Decimal("50"),
                quantity_received=Decimal("0"),
                unit_price=Decimal("128.75"),
            ),
        ],
    )


def make_invoice(tax_id: str, items: list[InvoiceItem]) -> Invoice:
    return Invoice(
        source_system=SourceSystem.ALFA,
        po_number="4500001234",
        vendor=Vendor(tax_id=tax_id, name="Metalúrgica São Jorge S.A."),
        items=items,
    )


class TestCompliantInvoice:
    def test_no_discrepancies_when_everything_matches(self, order: PurchaseOrder):
        invoice = make_invoice(
            ORDER_VENDOR_TAX_ID,
            [InvoiceItem(material="MAT-1001", quantity=Decimal("40"), total_value=Decimal("1836.00"))],
        )
        result = check(order, invoice)
        assert result.status == CheckStatus.COMPLIANT
        assert result.discrepancies == []

    def test_masked_vendor_tax_id_is_tolerated(self, order: PurchaseOrder):
        """Diferença de representação (máscara de CNPJ) não é divergência (RF5.4)."""
        invoice = make_invoice(
            "23.456.789/0001-01",
            [InvoiceItem(material="MAT-1001", quantity=Decimal("40"), total_value=Decimal("1836.00"))],
        )
        result = check(order, invoice)
        assert result.status == CheckStatus.COMPLIANT

    def test_quantity_exactly_equal_to_pending_is_not_a_violation(self, order: PurchaseOrder):
        invoice = make_invoice(
            ORDER_VENDOR_TAX_ID,
            [InvoiceItem(material="MAT-1001", quantity=Decimal("40"), total_value=Decimal("1836.00"))],
        )
        result = check(order, invoice)
        assert not any(
            d.type == DivergenceType.QUANTITY_EXCEEDS_PENDING for d in result.discrepancies
        )


class TestVendorMismatch:
    def test_different_tax_id_is_flagged(self, order: PurchaseOrder):
        invoice = make_invoice(
            "99999999000199",
            [InvoiceItem(material="MAT-1001", quantity=Decimal("10"), total_value=Decimal("459.00"))],
        )
        result = check(order, invoice)
        assert result.status == CheckStatus.DIVERGENT
        [discrepancy] = [
            d for d in result.discrepancies if d.type == DivergenceType.VENDOR_MISMATCH
        ]
        assert discrepancy.expected == ORDER_VENDOR_TAX_ID
        assert discrepancy.actual == "99999999000199"


class TestMaterialNotInOrder:
    def test_unknown_material_is_flagged(self, order: PurchaseOrder):
        invoice = make_invoice(
            ORDER_VENDOR_TAX_ID,
            [InvoiceItem(material="MAT-9999", quantity=Decimal("5"), total_value=Decimal("100.00"))],
        )
        result = check(order, invoice)
        assert result.status == CheckStatus.DIVERGENT
        [discrepancy] = result.discrepancies
        assert discrepancy.type == DivergenceType.MATERIAL_NOT_IN_ORDER
        assert discrepancy.material == "MAT-9999"


class TestQuantityExceedsPending:
    def test_quantity_above_pending_is_flagged(self, order: PurchaseOrder):
        # Pendente de MAT-1001 = 100 - 60 = 40
        invoice = make_invoice(
            ORDER_VENDOR_TAX_ID,
            [InvoiceItem(material="MAT-1001", quantity=Decimal("41"), total_value=Decimal("1881.90"))],
        )
        result = check(order, invoice)
        [discrepancy] = [
            d for d in result.discrepancies if d.type == DivergenceType.QUANTITY_EXCEEDS_PENDING
        ]
        assert discrepancy.expected == "40"
        assert discrepancy.actual == "41"


class TestPriceMismatch:
    def test_total_value_different_from_expected_is_flagged(self, order: PurchaseOrder):
        # Esperado: 40 * 45.9 = 1836.00
        invoice = make_invoice(
            ORDER_VENDOR_TAX_ID,
            [InvoiceItem(material="MAT-1001", quantity=Decimal("40"), total_value=Decimal("2000.00"))],
        )
        result = check(order, invoice)
        [discrepancy] = result.discrepancies
        assert discrepancy.type == DivergenceType.PRICE_MISMATCH
        assert discrepancy.expected == "1836.00"
        assert discrepancy.actual == "2000.00"

    def test_rounding_eliminates_representation_noise_not_business_tolerance(
        self, order: PurchaseOrder
    ):
        """RN5: arredonda só para tirar ruído de representação; diferença real continua divergência."""
        # 1 * 45.9 = 45.90 exato -> conforme mesmo com total_value tendo mais casas decimais
        invoice = make_invoice(
            ORDER_VENDOR_TAX_ID,
            [InvoiceItem(material="MAT-1001", quantity=Decimal("1"), total_value=Decimal("45.900"))],
        )
        result = check(order, invoice)
        assert not any(d.type == DivergenceType.PRICE_MISMATCH for d in result.discrepancies)

        # mas um centavo de diferença real ainda é divergência
        invoice_off_by_a_cent = make_invoice(
            ORDER_VENDOR_TAX_ID,
            [InvoiceItem(material="MAT-1001", quantity=Decimal("1"), total_value=Decimal("45.91"))],
        )
        result = check(order, invoice_off_by_a_cent)
        assert any(d.type == DivergenceType.PRICE_MISMATCH for d in result.discrepancies)


class TestMultipleSimultaneousDiscrepancies:
    def test_all_discrepancies_are_reported_together(self, order: PurchaseOrder):
        invoice = make_invoice(
            "11111111000111",  # fornecedor errado
            [
                # quantidade acima do pendente (40) e preço incompatível
                InvoiceItem(material="MAT-1001", quantity=Decimal("999"), total_value=Decimal("1.00")),
                # material inexistente
                InvoiceItem(material="MAT-XXXX", quantity=Decimal("1"), total_value=Decimal("1.00")),
            ],
        )
        result = check(order, invoice)

        assert result.status == CheckStatus.DIVERGENT
        types = {d.type for d in result.discrepancies}
        assert types == {
            DivergenceType.VENDOR_MISMATCH,
            DivergenceType.MATERIAL_NOT_IN_ORDER,
            DivergenceType.QUANTITY_EXCEEDS_PENDING,
            DivergenceType.PRICE_MISMATCH,
        }
        assert len(result.discrepancies) == 4
