from fastapi import FastAPI

from app.api.routers import ingestion, invoice_checks, purchase_orders

app = FastAPI(title="Conector de Pedidos de Compra V360")

app.include_router(ingestion.router)
app.include_router(purchase_orders.router)
app.include_router(invoice_checks.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
