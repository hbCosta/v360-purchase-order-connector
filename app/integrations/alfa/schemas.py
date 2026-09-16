from pydantic import BaseModel


class AlfaVendorPayload(BaseModel):
    """Fornecedor no formato bruto do Alfa (requirements.md §9)."""

    tax_id: str
    name: str


class AlfaItemPayload(BaseModel):
    """Item de pedido no formato bruto do Alfa.

    `quantity_ordered`/`quantity_received`/`unit_price` ficam como `int | float` (o tipo nativo
    que o parser JSON já entrega) para que o adapter converta para `Decimal` via `parse_decimal`
    sem herdar erro de ponto flutuante (design.md §5.2, §6.1).
    """

    line: int
    material: str
    description: str
    uom: str
    quantity_ordered: int | float
    quantity_received: int | float = 0  # suposição S2: ausente -> 0
    unit_price: int | float


class AlfaPurchaseOrderPayload(BaseModel):
    """Pedido de compra no formato bruto do Alfa."""

    po_number: str
    created_at: str
    status: str
    currency: str
    vendor: AlfaVendorPayload
    items: list[AlfaItemPayload]


class AlfaIngestionPayload(BaseModel):
    """Envelope do payload de ingestão do Alfa: `POST /ingestion/alfa`."""

    purchase_orders: list[AlfaPurchaseOrderPayload]
