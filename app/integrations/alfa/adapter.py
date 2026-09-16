from app.domain.enums import OrderStatus, SourceSystem
from app.domain.exceptions import AdapterParsingError
from app.domain.models import PurchaseOrder, PurchaseOrderItem, Vendor
from app.integrations.alfa.schemas import (
    AlfaIngestionPayload,
    AlfaItemPayload,
    AlfaPurchaseOrderPayload,
)
from app.normalization.dates import parse_iso_date
from app.normalization.documents import normalize_tax_id
from app.normalization.money import parse_decimal

ALFA_STATUS_MAP: dict[str, OrderStatus] = {
    "open": OrderStatus.OPEN,
    "closed": OrderStatus.CLOSED,
    "blocked": OrderStatus.BLOCKED,
}


def parse_orders(payload: AlfaIngestionPayload) -> list[PurchaseOrder]:
    """Converte o payload bruto do Alfa para o modelo canônico (RF1)."""
    return [_parse_order(po) for po in payload.purchase_orders]


def _parse_order(po: AlfaPurchaseOrderPayload) -> PurchaseOrder:
    return PurchaseOrder(
        source_system=SourceSystem.ALFA,
        po_number=po.po_number,
        created_at=parse_iso_date(po.created_at),
        status=_map_status(po.status),
        currency=po.currency,
        vendor=Vendor(tax_id=normalize_tax_id(po.vendor.tax_id), name=po.vendor.name),
        items=[_parse_item(item) for item in po.items],
    )


def _parse_item(item: AlfaItemPayload) -> PurchaseOrderItem:
    return PurchaseOrderItem(
        line=item.line,
        material=item.material,
        description=item.description,
        uom=item.uom,
        quantity_ordered=parse_decimal(item.quantity_ordered),
        quantity_received=parse_decimal(item.quantity_received),
        unit_price=parse_decimal(item.unit_price),
    )


def _map_status(raw_status: str) -> OrderStatus:
    try:
        return ALFA_STATUS_MAP[raw_status]
    except KeyError:
        raise AdapterParsingError(
            f"Situação desconhecida do Alfa: {raw_status!r}. Esperado um de {sorted(ALFA_STATUS_MAP)}."
        ) from None
