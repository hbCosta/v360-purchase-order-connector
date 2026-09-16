import pytest
from fastapi.testclient import TestClient

ALFA_PAYLOAD = {
    "purchase_orders": [
        {
            "po_number": "4500001234",
            "created_at": "2026-08-05",
            "status": "open",
            "currency": "BRL",
            "vendor": {"tax_id": "23456789000101", "name": "Metalúrgica São Jorge S.A."},
            "items": [
                {
                    "line": 10,
                    "material": "MAT-1001",
                    "description": "Chapa de aço 2mm",
                    "uom": "UN",
                    "quantity_ordered": 100,
                    "quantity_received": 60,
                    "unit_price": 45.9,
                }
            ],
        }
    ]
}

BETA_CABECALHO_CSV = (
    "NUMERO_PEDIDO;FORNECEDOR_CNPJ;FORNECEDOR_RAZAO_SOCIAL;EMISSAO;SITUACAO;MOEDA\n"
    "20260088412;12.345.678/0001-90;Distribuidora Horizonte Ltda;15/08/2026;EM ABERTO;BRL\n"
    "20260088413;98.765.432/0001-55;Frigorífico Boa Mesa S.A.;01/08/2026;BLOQUEADO;BRL\n"
)

BETA_ITENS_CSV = (
    "NUMERO_PEDIDO;ITEM;CODIGO_MATERIAL;DESCRICAO;UNIDADE;QTD_PEDIDA;QTD_RECEBIDA;PRECO_UNITARIO\n"
    "20260088412;1;MAT-77;Óleo de soja 900ml;UN;1.200,000;400,000;6,49\n"
    "20260088413;1;MAT-91;Carne bovina dianteiro kg;KG;2.000,000;2.000,000;27,90\n"
)


def _ingest_beta(client: TestClient):
    return client.post(
        "/ingestion/beta",
        files={
            "cabecalho": ("cabecalho.csv", BETA_CABECALHO_CSV.encode("utf-8"), "text/csv"),
            "itens": ("itens.csv", BETA_ITENS_CSV.encode("utf-8"), "text/csv"),
        },
    )


@pytest.fixture
def ingested_client(client: TestClient) -> TestClient:
    """Ingere um pedido do Alfa e dois do Beta (um deles totalmente recebido)."""
    resp = client.post("/ingestion/alfa", json=ALFA_PAYLOAD)
    assert resp.status_code == 201
    resp = _ingest_beta(client)
    assert resp.status_code == 201
    return client


class TestIngestionEndpoints:
    def test_ingest_alfa_returns_summary(self, client: TestClient):
        resp = client.post("/ingestion/alfa", json=ALFA_PAYLOAD)
        assert resp.status_code == 201
        assert resp.json() == {"source_system": "alfa", "orders_ingested": 1, "items_ingested": 1}

    def test_ingest_beta_returns_summary(self, client: TestClient):
        resp = _ingest_beta(client)
        assert resp.status_code == 201
        assert resp.json() == {"source_system": "beta", "orders_ingested": 2, "items_ingested": 2}

    def test_ingest_alfa_unknown_status_returns_400(self, client: TestClient):
        payload = {
            "purchase_orders": [{**ALFA_PAYLOAD["purchase_orders"][0], "status": "cancelled"}]
        }
        resp = client.post("/ingestion/alfa", json=payload)
        assert resp.status_code == 400

    def test_ingest_alfa_malformed_json_structure_returns_422(self, client: TestClient):
        resp = client.post("/ingestion/alfa", json={"campo_errado": []})
        assert resp.status_code == 422


class TestListPurchaseOrders:
    def test_list_without_filter_returns_all_orders(self, ingested_client: TestClient):
        resp = ingested_client.get("/purchase-orders")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_filter_by_source_system(self, ingested_client: TestClient):
        resp = ingested_client.get("/purchase-orders", params={"source_system": "beta"})
        po_numbers = {o["po_number"] for o in resp.json()}
        assert po_numbers == {"20260088412", "20260088413"}

    def test_filter_by_status(self, ingested_client: TestClient):
        resp = ingested_client.get("/purchase-orders", params={"status": "blocked"})
        assert [o["po_number"] for o in resp.json()] == ["20260088413"]

    def test_filter_by_vendor_tax_id_accepts_masked_input(self, ingested_client: TestClient):
        resp = ingested_client.get(
            "/purchase-orders", params={"vendor_tax_id": "12.345.678/0001-90"}
        )
        assert [o["po_number"] for o in resp.json()] == ["20260088412"]

    def test_filter_has_pending_true_excludes_fully_received_orders(
        self, ingested_client: TestClient
    ):
        resp = ingested_client.get("/purchase-orders", params={"has_pending": "true"})
        po_numbers = {o["po_number"] for o in resp.json()}
        assert po_numbers == {"4500001234", "20260088412"}

    def test_filter_has_pending_false_returns_fully_received_orders(
        self, ingested_client: TestClient
    ):
        resp = ingested_client.get("/purchase-orders", params={"has_pending": "false"})
        assert [o["po_number"] for o in resp.json()] == ["20260088413"]


class TestGetPurchaseOrderDetail:
    def test_returns_order_with_items_and_pending_quantity(self, ingested_client: TestClient):
        resp = ingested_client.get("/purchase-orders/alfa/4500001234")
        assert resp.status_code == 200
        body = resp.json()
        assert body["po_number"] == "4500001234"
        assert len(body["items"]) == 1
        assert body["items"][0]["quantity_ordered"] == "100"
        assert body["items"][0]["quantity_received"] == "60"
        assert body["items"][0]["quantity_pending"] == "40"

    def test_returns_404_for_unknown_order(self, ingested_client: TestClient):
        resp = ingested_client.get("/purchase-orders/alfa/9999999")
        assert resp.status_code == 404
