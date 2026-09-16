from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.domain.enums import SourceSystem
from app.domain.models import Vendor


class InvoiceItem(BaseModel):
    """Item de uma nota fiscal enviada pela V360 para conferência (RF5.1)."""

    model_config = ConfigDict(frozen=True)

    material: str
    quantity: Decimal
    total_value: Decimal


class Invoice(BaseModel):
    """Nota fiscal a ser conferida contra um pedido já ingerido (RF5.1, suposição S4)."""

    model_config = ConfigDict(frozen=True)

    source_system: SourceSystem
    po_number: str
    vendor: Vendor
    items: list[InvoiceItem]
