from fastapi import APIRouter

from app.api.schemas.report import ReportResponse
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/invoice-checks")
def get_invoice_checks_report() -> ReportResponse:
    """Relatório agregado das conferências já realizadas: conformes, divergentes e por tipo (RF6)."""
    summary = report_service.summarize()
    return ReportResponse.model_validate(summary)
