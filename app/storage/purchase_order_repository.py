from app.domain.enums import OrderStatus, SourceSystem
from app.domain.models import PurchaseOrder


class PurchaseOrderRepository:
    """Armazenamento em memória de pedidos de compra (design.md §11).

    Chave: par (source_system, po_number) — a identidade de negócio do pedido (RN3). Não valida
    regra de negócio; filtros recebem valores já normalizados (ex.: `vendor_tax_id` sem máscara).
    """

    def __init__(self) -> None:
        self._orders: dict[tuple[SourceSystem, str], PurchaseOrder] = {}

    def upsert(self, order: PurchaseOrder) -> None:
        """Insere ou substitui um pedido pela sua chave (RN7 — reingestão substitui o anterior)."""
        self._orders[(order.source_system, order.po_number)] = order

    def get(self, source_system: SourceSystem, po_number: str) -> PurchaseOrder | None:
        return self._orders.get((source_system, po_number))

    def clear(self) -> None:
        """Remove todos os pedidos armazenados. Uso principal: isolar testes entre si."""
        self._orders.clear()

    def list(
        self,
        source_system: SourceSystem | None = None,
        vendor_tax_id: str | None = None,
        status: OrderStatus | None = None,
        has_pending: bool | None = None,
    ) -> list[PurchaseOrder]:
        orders = self._orders.values()

        if source_system is not None:
            orders = (o for o in orders if o.source_system == source_system)
        if vendor_tax_id is not None:
            orders = (o for o in orders if o.vendor.tax_id == vendor_tax_id)
        if status is not None:
            orders = (o for o in orders if o.status == status)
        if has_pending is not None:
            orders = (o for o in orders if _has_pending_item(o) == has_pending)

        return list(orders)


def _has_pending_item(order: PurchaseOrder) -> bool:
    return any(item.quantity_pending > 0 for item in order.items)


purchase_order_repository = PurchaseOrderRepository()
