from app.domain.discrepancies import InvoiceCheckResult
from app.domain.enums import CheckStatus, SourceSystem


class InvoiceCheckRepository:
    """Histórico em memória de conferências de nota fiscal já realizadas (design.md §11).

    `list()` aceita filtros opcionais — sem nenhum, devolve o histórico inteiro (comportamento
    usado por `report_service`, que sempre lê tudo para agregar).
    """

    def __init__(self) -> None:
        self._results: list[InvoiceCheckResult] = []

    def append(self, result: InvoiceCheckResult) -> None:
        self._results.append(result)

    def list(
        self,
        source_system: SourceSystem | None = None,
        po_number: str | None = None,
        status: CheckStatus | None = None,
    ) -> list[InvoiceCheckResult]:
        results = self._results
        if source_system is not None:
            results = [r for r in results if r.source_system == source_system]
        if po_number is not None:
            results = [r for r in results if r.po_number == po_number]
        if status is not None:
            results = [r for r in results if r.status == status]
        return list(results)

    def clear(self) -> None:
        """Remove todos os resultados armazenados. Uso principal: isolar testes entre si."""
        self._results.clear()


invoice_check_repository = InvoiceCheckRepository()
