from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import CheckStatus, DivergenceType, SourceSystem


class Discrepancy(BaseModel):
    """Uma divergência de negócio encontrada em uma conferência (RF5.2, design.md §8).

    O formato é genérico (mesmos 4 campos para qualquer tipo) de propósito: adicionar um novo
    `DivergenceType` não exige uma nova classe nem migração de schema (decisão D7).
    """

    model_config = ConfigDict(frozen=True)

    type: DivergenceType
    message: str
    material: str | None = None
    expected: str | None = None
    actual: str | None = None


class InvoiceCheckResult(BaseModel):
    """Resultado estruturado de uma conferência de nota fiscal (RF5.2)."""

    model_config = ConfigDict(frozen=True)

    source_system: SourceSystem
    po_number: str
    status: CheckStatus
    discrepancies: list[Discrepancy] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
