from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, ValidationError

from app.domain.enums import SourceSystem
from app.domain.exceptions import AdapterParsingError
from app.domain.models import PurchaseOrder
from app.integrations.alfa import adapter as alfa_adapter
from app.integrations.alfa.schemas import AlfaIngestionPayload
from app.integrations.beta import adapter as beta_adapter
from app.integrations.gama import adapter as gama_adapter
from app.integrations.gama.schemas import GamaItemRow
from app.storage.purchase_order_repository import purchase_order_repository

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


class IngestionSummary(BaseModel):
    """Resumo de uma ingestão: quantos pedidos e itens foram armazenados no modelo canônico."""

    source_system: SourceSystem
    orders_ingested: int
    items_ingested: int


def _store_and_summarize(
    source_system: SourceSystem, orders: list[PurchaseOrder]
) -> IngestionSummary:
    for order in orders:
        purchase_order_repository.upsert(order)
    return IngestionSummary(
        source_system=source_system,
        orders_ingested=len(orders),
        items_ingested=sum(len(order.items) for order in orders),
    )


@router.post("/alfa", status_code=201)
def ingest_alfa(payload: AlfaIngestionPayload) -> IngestionSummary:
    """Recebe o JSON do Alfa, normaliza para o modelo canônico e armazena (RF1)."""
    try:
        orders = alfa_adapter.parse_orders(payload)
    except (AdapterParsingError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _store_and_summarize(SourceSystem.ALFA, orders)


@router.post("/beta", status_code=201)
async def ingest_beta(
    cabecalho: UploadFile = File(..., description="cabecalho.csv"),
    itens: UploadFile = File(..., description="itens.csv"),
) -> IngestionSummary:
    """Recebe os dois CSVs do Beta, normaliza para o modelo canônico e armazena (RF2)."""
    header_text = (await cabecalho.read()).decode("utf-8")
    items_text = (await itens.read()).decode("utf-8")
    try:
        orders = beta_adapter.parse_orders(header_text, items_text)
    except (AdapterParsingError, ValueError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _store_and_summarize(SourceSystem.BETA, orders)


@router.post("/gama", status_code=201)
def ingest_gama(payload: list[GamaItemRow]) -> IngestionSummary:
    """Recebe o JSON achatado do Gama, normaliza para o modelo canônico e armazena (RF7)."""
    try:
        orders = gama_adapter.parse_orders(payload)
    except (AdapterParsingError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _store_and_summarize(SourceSystem.GAMA, orders)
