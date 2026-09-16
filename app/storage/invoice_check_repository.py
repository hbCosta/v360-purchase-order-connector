from app.domain.discrepancies import InvoiceCheckResult


class InvoiceCheckRepository:
    """Histórico em memória de conferências de nota fiscal já realizadas (design.md §11).

    Sem filtros em `list()`: nem o contrato da API (design.md §9) nem RF6 pedem algum para o
    histórico — `report_service` (T31) lê tudo para agregar.
    """

    def __init__(self) -> None:
        self._results: list[InvoiceCheckResult] = []

    def append(self, result: InvoiceCheckResult) -> None:
        self._results.append(result)

    def list(self) -> list[InvoiceCheckResult]:
        return list(self._results)

    def clear(self) -> None:
        """Remove todos os resultados armazenados. Uso principal: isolar testes entre si."""
        self._results.clear()


invoice_check_repository = InvoiceCheckRepository()
