import csv
import io

from app.domain.enums import OrderStatus, SourceSystem
from app.domain.exceptions import AdapterParsingError
from app.domain.models import PurchaseOrder, PurchaseOrderItem, Vendor
from app.integrations.beta.schemas import BetaHeaderRow, BetaItemRow
from app.normalization.dates import parse_br_date
from app.normalization.documents import normalize_tax_id
from app.normalization.money import parse_br_decimal

BETA_STATUS_MAP: dict[str, OrderStatus] = {
    "EM ABERTO": OrderStatus.OPEN,
    "ENCERRADO": OrderStatus.CLOSED,  # suposição S7 — termo não aparece nas amostras do enunciado
    "BLOQUEADO": OrderStatus.BLOCKED,
}


def parse_orders(header_csv_text: str, items_csv_text: str) -> list[PurchaseOrder]:
    """Converte os dois CSVs do Beta, relacionados por `NUMERO_PEDIDO`, para o modelo canônico (RF2)."""
    headers = [
        BetaHeaderRow.model_validate(row)
        for row in csv.DictReader(io.StringIO(header_csv_text), delimiter=";")
    ]
    items_by_order = _group_items_by_order(items_csv_text)

    known_order_numbers = {header.numero_pedido for header in headers}
    for numero_pedido in items_by_order:
        if numero_pedido not in known_order_numbers:
            raise AdapterParsingError(
                f"itens.csv referencia o pedido {numero_pedido!r}, que não existe em cabecalho.csv."
            )

    return [
        _parse_order(header, items_by_order.get(header.numero_pedido, []))
        for header in headers
    ]


def _group_items_by_order(items_csv_text: str) -> dict[str, list[BetaItemRow]]:
    grouped: dict[str, list[BetaItemRow]] = {}
    for row in csv.DictReader(io.StringIO(items_csv_text), delimiter=";"):
        item = BetaItemRow.model_validate(row)
        grouped.setdefault(item.numero_pedido, []).append(item)
    return grouped


def _parse_order(header: BetaHeaderRow, items: list[BetaItemRow]) -> PurchaseOrder:
    return PurchaseOrder(
        source_system=SourceSystem.BETA,
        po_number=header.numero_pedido,
        created_at=parse_br_date(header.emissao),
        status=_map_status(header.situacao),
        currency=header.moeda,
        vendor=Vendor(
            tax_id=normalize_tax_id(header.fornecedor_cnpj),
            name=header.fornecedor_razao_social,
        ),
        items=[_parse_item(item) for item in items],
    )


def _parse_item(item: BetaItemRow) -> PurchaseOrderItem:
    return PurchaseOrderItem(
        line=int(item.item),
        material=item.codigo_material,
        description=item.descricao,
        uom=item.unidade,
        quantity_ordered=parse_br_decimal(item.qtd_pedida),
        quantity_received=parse_br_decimal(item.qtd_recebida),
        unit_price=parse_br_decimal(item.preco_unitario),
    )


def _map_status(raw_status: str) -> OrderStatus:
    try:
        return BETA_STATUS_MAP[raw_status]
    except KeyError:
        raise AdapterParsingError(
            f"Situação desconhecida do Beta: {raw_status!r}. Esperado um de {sorted(BETA_STATUS_MAP)}."
        ) from None
