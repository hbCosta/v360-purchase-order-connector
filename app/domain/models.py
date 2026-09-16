from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import OrderStatus, SourceSystem


class Vendor(BaseModel):
    """Fornecedor de um pedido de compra, com `tax_id` já normalizado (RN4)."""

    model_config = ConfigDict(frozen=True)

    tax_id: str
    name: str


class PurchaseOrderItem(BaseModel):
    """Item (linha) de um pedido, já expresso na unidade de estoque (design.md §5.5)."""

    model_config = ConfigDict(frozen=True)

    line: int
    material: str
    description: str
    uom: str
    quantity_ordered: Decimal
    quantity_received: Decimal
    unit_price: Decimal

    @property
    def quantity_pending(self) -> Decimal:
        """Saldo pendente do item: sempre calculado, nunca armazenado (RN2)."""
        return self.quantity_ordered - self.quantity_received


class PurchaseOrder(BaseModel):
    """Pedido de compra no modelo canônico — a única representação que domain/services/api conhecem."""

    model_config = ConfigDict(frozen=True)

    source_system: SourceSystem
    po_number: str
    created_at: date
    status: OrderStatus
    currency: str
    vendor: Vendor
    items: list[PurchaseOrderItem] = Field(default_factory=list)

    @property
    def id(self) -> str:
        """Identidade do pedido: par (source_system, po_number), nunca po_number isolado (RN3)."""
        return f"{self.source_system.value}:{self.po_number}"
