from fastapi import APIRouter, HTTPException

from app.api.schemas.invoice_check import InvoiceCheckRequest, InvoiceCheckResponse
from app.domain.enums import CheckStatus, SourceSystem
from app.domain.exceptions import PurchaseOrderNotFoundError
from app.domain.invoice import Invoice, InvoiceItem
from app.domain.models import Vendor
from app.services import invoice_check_service, purchase_order_service
from app.storage.invoice_check_repository import invoice_check_repository

router = APIRouter(prefix="/invoice-checks", tags=["invoice-checks"])


@router.post("")
def create_invoice_check(payload: InvoiceCheckRequest) -> InvoiceCheckResponse:
    """Confere uma nota fiscal contra um pedido já ingerido (RF5).

    Sempre `200`, mesmo quando o resultado é divergente — `DIVERGENT` é um valor de negócio na
    resposta, não uma falha HTTP (design.md §9). `404` é reservado para o pedido não existir.
    """
    try:
        order = purchase_order_service.get_order(payload.source_system, payload.po_number)
    except PurchaseOrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    invoice = Invoice(
        source_system=payload.source_system,
        po_number=payload.po_number,
        vendor=Vendor(tax_id=payload.vendor.tax_id, name=payload.vendor.name),
        items=[
            InvoiceItem(
                material=item.material, quantity=item.quantity, total_value=item.total_value
            )
            for item in payload.items
        ],
    )

    result = invoice_check_service.check(order, invoice)
    invoice_check_repository.append(result)
    return InvoiceCheckResponse.model_validate(result)


@router.get("")
def list_invoice_checks(
    source_system: SourceSystem | None = None,
    po_number: str | None = None,
    status: CheckStatus | None = None,
) -> list[InvoiceCheckResponse]:
    """Histórico de conferências já realizadas, com filtros opcionais (apoio a RF6).

    Sem filtro nenhum, devolve o histórico inteiro — o comportamento de antes é preservado.
    """
    results = invoice_check_repository.list(
        source_system=source_system, po_number=po_number, status=status
    )
    return [InvoiceCheckResponse.model_validate(result) for result in results]
