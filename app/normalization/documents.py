import re

_NON_DIGITS = re.compile(r"\D")


def normalize_tax_id(value: str) -> str:
    """Normaliza um CNPJ para a forma canônica: apenas dígitos, sem máscara (RN4, design.md §5.3).

    `"12.345.678/0001-90"` e `"12345678000190"` produzem o mesmo resultado, permitindo comparação
    por igualdade simples em `invoice_check_service` sem lógica adicional.
    """
    return _NON_DIGITS.sub("", value)
