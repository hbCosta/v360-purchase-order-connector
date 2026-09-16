from pydantic import BaseModel, ConfigDict

from app.domain.enums import DivergenceType


class ReportResponse(BaseModel):
    """Resposta de `GET /reports/invoice-checks` (RF6)."""

    model_config = ConfigDict(from_attributes=True)

    total: int
    compliant_count: int
    divergent_count: int
    discrepancy_type_counts: dict[DivergenceType, int]
