from collections import defaultdict

from app.domain.enums import OrderStatus, SourceSystem
from app.domain.exceptions import AdapterParsingError
from app.domain.models import PurchaseOrder, PurchaseOrderItem, Vendor
from app.integrations.gama.schemas import GamaItemRow
from app.normalization.dates import parse_unix_timestamp
from app.normalization.documents import normalize_tax_id
from app.normalization.money import cents_to_decimal, parse_decimal

GAMA_STATUS_MAP: dict[int, OrderStatus] = {
    1: OrderStatus.OPEN,
    2: OrderStatus.CLOSED,
    3: OrderStatus.BLOCKED,
}


def parse_orders(payload: list[GamaItemRow]) -> list[PurchaseOrder]:
    """Converte o JSON achatado do Gama para o modelo canônico (RF7).

    Não existe cabeçalho separado: os dados do pedido se repetem em cada linha de item — usa-se
    os valores da primeira linha de cada grupo. Ainda sem conversão de unidade de compra (T42).
    """
    grouped: dict[str, list[GamaItemRow]] = defaultdict(list)
    for row in payload:
        grouped[row.ped].append(row)

    return [_parse_order(po_number, rows) for po_number, rows in grouped.items()]


def _parse_order(po_number: str, rows: list[GamaItemRow]) -> PurchaseOrder:
    header = rows[0]
    return PurchaseOrder(
        source_system=SourceSystem.GAMA,
        po_number=po_number,
        created_at=parse_unix_timestamp(header.dt_criacao),
        status=_map_status(header.situacao),
        currency="BRL",  # suposição S1 — Gama não informa moeda no payload
        vendor=Vendor(
            tax_id=normalize_tax_id(header.cnpj_fornecedor),
            name=header.nome_fornecedor,
        ),
        items=[_parse_item(row) for row in rows],
    )


def _parse_item(row: GamaItemRow) -> PurchaseOrderItem:
    return PurchaseOrderItem(
        line=row.item,
        material=row.cod_mat,
        description=row.desc_mat,
        uom=row.um,
        quantity_ordered=parse_decimal(row.qtd_ped),
        quantity_received=parse_decimal(row.qtd_rec),
        unit_price=cents_to_decimal(row.preco_unit_centavos),
    )


def _map_status(situacao: int) -> OrderStatus:
    try:
        return GAMA_STATUS_MAP[situacao]
    except KeyError:
        raise AdapterParsingError(
            f"Situação desconhecida do Gama: {situacao!r}. Esperado um de {sorted(GAMA_STATUS_MAP)}."
        ) from None
