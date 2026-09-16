from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.domain.enums import OrderStatus, SourceSystem


class VendorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tax_id: str
    name: str


class PurchaseOrderItemResponse(BaseModel):
    """DTO de item de pedido. `quantity_pending` é lido da propriedade computada do domínio (RN2)."""

    model_config = ConfigDict(from_attributes=True)

    line: int
    material: str
    description: str
    uom: str
    quantity_ordered: Decimal
    quantity_received: Decimal
    quantity_pending: Decimal
    unit_price: Decimal


class PurchaseOrderResponse(BaseModel):
    """DTO de pedido — usado tanto na listagem (RF4.1) quanto no detalhe (RF4.2).

    Uma única forma para os dois usos: o volume de dados de um projeto demonstrativo não
    justifica manter um schema de listagem "enxuto" separado do de detalhe (RNF4).
    """

    model_config = ConfigDict(from_attributes=True)

    source_system: SourceSystem
    po_number: str
    created_at: date
    status: OrderStatus
    currency: str
    vendor: VendorResponse
    items: list[PurchaseOrderItemResponse]
