from collections import Counter

from pydantic import BaseModel

from app.domain.enums import CheckStatus, DivergenceType
from app.storage.invoice_check_repository import invoice_check_repository


class ReportSummary(BaseModel):
    """Agregação das conferências de nota fiscal já realizadas (RF6)."""

    total: int
    compliant_count: int
    divergent_count: int
    discrepancy_type_counts: dict[DivergenceType, int]


def summarize() -> ReportSummary:
    """Lê todo o histórico de conferências e agrega conformes/divergentes/tipos (design.md §7.3)."""
    results = invoice_check_repository.list()

    compliant_count = sum(1 for result in results if result.status == CheckStatus.COMPLIANT)
    divergent_count = sum(1 for result in results if result.status == CheckStatus.DIVERGENT)

    type_counter: Counter[DivergenceType] = Counter()
    for result in results:
        for discrepancy in result.discrepancies:
            type_counter[discrepancy.type] += 1

    return ReportSummary(
        total=len(results),
        compliant_count=compliant_count,
        divergent_count=divergent_count,
        discrepancy_type_counts=dict(type_counter),
    )
