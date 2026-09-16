from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.domain.enums import CheckStatus, DivergenceType, SourceSystem


class InvoiceVendorRequest(BaseModel):
    tax_id: str
    name: str


class InvoiceItemRequest(BaseModel):
    material: str
    quantity: Decimal
    total_value: Decimal


class InvoiceCheckRequest(BaseModel):
    """Corpo de `POST /invoice-checks`: dados da nota fiscal enviados pela V360 (RF5.1)."""

    source_system: SourceSystem
    po_number: str
    vendor: InvoiceVendorRequest
    items: list[InvoiceItemRequest]


class DiscrepancyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: DivergenceType
    message: str
    material: str | None = None
    expected: str | None = None
    actual: str | None = None


class InvoiceCheckResponse(BaseModel):
    """Resultado estruturado de uma conferência — nunca um booleano simples (RF5.2)."""

    model_config = ConfigDict(from_attributes=True)

    source_system: SourceSystem
    po_number: str
    status: CheckStatus
    discrepancies: list[DiscrepancyResponse]
    checked_at: datetime
