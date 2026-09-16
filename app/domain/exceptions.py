from app.domain.enums import SourceSystem


class PurchaseOrderNotFoundError(Exception):
    """Levantada quando um pedido referenciado por (source_system, po_number) não existe.

    Tratada pelo router como HTTP 404 — erro de pré-condição, não divergência de negócio (A3).
    """

    def __init__(self, source_system: SourceSystem, po_number: str) -> None:
        self.source_system = source_system
        self.po_number = po_number
        super().__init__(
            f"Pedido {po_number!r} do sistema {source_system.value!r} não foi encontrado."
        )


class AdapterParsingError(Exception):
    """Levantada por um adapter ao encontrar um dado fora do vocabulário/formato esperado.

    Ex.: um valor de situação sem mapeamento conhecido (RN1) — nunca é ignorado silenciosamente.
    """
