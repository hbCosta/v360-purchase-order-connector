from decimal import ROUND_HALF_UP, Decimal

from app.domain.discrepancies import Discrepancy, InvoiceCheckResult
from app.domain.enums import CheckStatus, DivergenceType
from app.domain.invoice import Invoice, InvoiceItem
from app.domain.models import PurchaseOrder
from app.normalization.documents import normalize_tax_id

_TWO_PLACES = Decimal("0.01")


def check(order: PurchaseOrder, invoice: Invoice) -> InvoiceCheckResult:
    """Confere uma nota fiscal contra um pedido de compra (RF5, design.md §7.2).

    Roda por completo — não para na primeira divergência — para que a V360 veja tudo o que não
    bate de uma vez só (RF5.2). Não depende da situação do pedido (ambiguidade A1) nem atualiza
    `quantity_received` (RN6, ambiguidade A2): é uma operação de leitura.
    """
    discrepancies: list[Discrepancy] = []

    vendor_discrepancy = _check_vendor(order, invoice)
    if vendor_discrepancy is not None:
        discrepancies.append(vendor_discrepancy)

    for invoice_item in invoice.items:
        discrepancies.extend(_check_item(order, invoice_item))

    status = CheckStatus.DIVERGENT if discrepancies else CheckStatus.COMPLIANT
    return InvoiceCheckResult(
        source_system=order.source_system,
        po_number=order.po_number,
        status=status,
        discrepancies=discrepancies,
    )


def _check_vendor(order: PurchaseOrder, invoice: Invoice) -> Discrepancy | None:
    invoice_tax_id = normalize_tax_id(invoice.vendor.tax_id)
    if invoice_tax_id == order.vendor.tax_id:
        return None
    return Discrepancy(
        type=DivergenceType.VENDOR_MISMATCH,
        message=(
            f"Fornecedor da nota ({invoice_tax_id}) difere do fornecedor do pedido "
            f"({order.vendor.tax_id})."
        ),
        expected=order.vendor.tax_id,
        actual=invoice_tax_id,
    )


def _check_item(order: PurchaseOrder, invoice_item: InvoiceItem) -> list[Discrepancy]:
    matched_items = [item for item in order.items if item.material == invoice_item.material]

    if not matched_items:
        return [
            Discrepancy(
                type=DivergenceType.MATERIAL_NOT_IN_ORDER,
                material=invoice_item.material,
                message=(
                    f"Material {invoice_item.material!r} não existe no pedido {order.po_number}."
                ),
            )
        ]

    discrepancies: list[Discrepancy] = []

    # Suposição S3: cada material aparece no máximo em uma linha por pedido. Se houver mais de
    # uma linha casada, o saldo pendente é somado, mas o preço esperado usa a primeira linha.
    pending_total = sum((item.quantity_pending for item in matched_items), start=Decimal("0"))
    if invoice_item.quantity > pending_total:
        discrepancies.append(
            Discrepancy(
                type=DivergenceType.QUANTITY_EXCEEDS_PENDING,
                material=invoice_item.material,
                message=(
                    f"Quantidade da nota ({invoice_item.quantity}) excede o saldo pendente "
                    f"({pending_total}) do material {invoice_item.material!r}."
                ),
                expected=str(pending_total),
                actual=str(invoice_item.quantity),
            )
        )

    expected_total = _round_money(matched_items[0].unit_price * invoice_item.quantity)
    actual_total = _round_money(invoice_item.total_value)
    if actual_total != expected_total:
        discrepancies.append(
            Discrepancy(
                type=DivergenceType.PRICE_MISMATCH,
                material=invoice_item.material,
                message=(
                    f"Valor da nota ({actual_total}) difere do esperado ({expected_total}) para "
                    f"o material {invoice_item.material!r}."
                ),
                expected=str(expected_total),
                actual=str(actual_total),
            )
        )

    return discrepancies


def _round_money(value: Decimal) -> Decimal:
    """Arredonda a 2 casas para eliminar ruído de representação decimal — não é tolerância de
    negócio (RN5): qualquer diferença remanescente ainda é divergência."""
    return value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
