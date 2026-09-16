from fastapi import FastAPI

app = FastAPI(title="Conector de Pedidos de Compra V360")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
