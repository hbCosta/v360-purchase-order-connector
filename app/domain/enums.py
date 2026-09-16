from enum import Enum


class SourceSystem(str, Enum):
    """Sistema de origem do pedido. Um valor por cliente integrado."""

    ALFA = "alfa"
    BETA = "beta"


class OrderStatus(str, Enum):
    """Situação canônica de um pedido de compra (RN1)."""

    OPEN = "open"
    CLOSED = "closed"
    BLOCKED = "blocked"


class DivergenceType(str, Enum):
    """Tipos de divergência encontrados em uma conferência de nota fiscal (RF5.3)."""

    VENDOR_MISMATCH = "VENDOR_MISMATCH"
    MATERIAL_NOT_IN_ORDER = "MATERIAL_NOT_IN_ORDER"
    QUANTITY_EXCEEDS_PENDING = "QUANTITY_EXCEEDS_PENDING"
    PRICE_MISMATCH = "PRICE_MISMATCH"


class CheckStatus(str, Enum):
    """Resultado geral de uma conferência de nota fiscal (RF5.2)."""

    COMPLIANT = "COMPLIANT"
    DIVERGENT = "DIVERGENT"
