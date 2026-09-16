from app.domain.enums import OrderStatus, SourceSystem
from app.domain.exceptions import PurchaseOrderNotFoundError
from app.domain.models import PurchaseOrder
from app.normalization.documents import normalize_tax_id
from app.storage.purchase_order_repository import purchase_order_repository


def list_orders(
    source_system: SourceSystem | None = None,
    vendor_tax_id: str | None = None,
    status: OrderStatus | None = None,
    has_pending: bool | None = None,
) -> list[PurchaseOrder]:
    """Lista pedidos canônicos com os filtros de RF4.1.

    `vendor_tax_id` é normalizado aqui (RN4) para que quem consulta a API possa informar o CNPJ
    com ou sem máscara — o repositório em si só compara igualdade sobre o valor já normalizado.
    """
    normalized_tax_id = normalize_tax_id(vendor_tax_id) if vendor_tax_id is not None else None
    return purchase_order_repository.list(
        source_system=source_system,
        vendor_tax_id=normalized_tax_id,
        status=status,
        has_pending=has_pending,
    )


def get_order(source_system: SourceSystem, po_number: str) -> PurchaseOrder:
    """Busca o detalhe de um pedido (RF4.2).

    Levanta `PurchaseOrderNotFoundError` se não existir, em vez de devolver `None` — centraliza a
    política de "não encontrado é erro" em um único lugar, reusado pelo endpoint de detalhe e
    pelo endpoint de conferência de nota fiscal (ambos precisam do mesmo pedido resolvido).
    """
    order = purchase_order_repository.get(source_system, po_number)
    if order is None:
        raise PurchaseOrderNotFoundError(source_system, po_number)
    return order
