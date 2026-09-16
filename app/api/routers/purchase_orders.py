from fastapi import APIRouter, HTTPException

from app.api.schemas.purchase_order import PurchaseOrderResponse
from app.domain.enums import OrderStatus, SourceSystem
from app.domain.exceptions import PurchaseOrderNotFoundError
from app.services import purchase_order_service

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])


@router.get("")
def list_purchase_orders(
    source_system: SourceSystem | None = None,
    vendor_tax_id: str | None = None,
    status: OrderStatus | None = None,
    has_pending: bool | None = None,
) -> list[PurchaseOrderResponse]:
    """Lista pedidos canônicos com filtros por origem, fornecedor, situação e saldo pendente (RF4.1)."""
    orders = purchase_order_service.list_orders(
        source_system=source_system,
        vendor_tax_id=vendor_tax_id,
        status=status,
        has_pending=has_pending,
    )
    return [PurchaseOrderResponse.model_validate(order) for order in orders]


@router.get("/{source_system}/{po_number}")
def get_purchase_order(source_system: SourceSystem, po_number: str) -> PurchaseOrderResponse:
    """Detalhe de um pedido, com itens e saldo pendente por item (RF4.2)."""
    try:
        order = purchase_order_service.get_order(source_system, po_number)
    except PurchaseOrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PurchaseOrderResponse.model_validate(order)
