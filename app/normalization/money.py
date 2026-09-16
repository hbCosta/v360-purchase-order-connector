from decimal import Decimal


def parse_decimal(value: int | float | str | Decimal) -> Decimal:
    """Converte um número (Alfa) para `Decimal` sem herdar erro de ponto flutuante.

    Um `float` é convertido via `str()` antes de `Decimal(...)`: `Decimal(str(45.9))` dá
    `Decimal('45.9')`, enquanto `Decimal(45.9)` herdaria o erro de representação binária do
    `float` (design.md §5.2).
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    return Decimal(value.strip())


def parse_br_decimal(value: str) -> Decimal:
    """Converte um número no padrão brasileiro (Beta), ex.: `"1.200,000"` → `Decimal("1200.000")`."""
    normalized = value.strip().replace(".", "").replace(",", ".")
    return Decimal(normalized)
