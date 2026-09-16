import pytest
from fastapi.testclient import TestClient

GAMA_PAYLOAD = [
    {
        "ped": "GL-778",
        "item": 1,
        "cnpj_fornecedor": "34567890000112",
        "nome_fornecedor": "Transportes Ideal ME",
        "dt_criacao": 1786752000,
        "cod_mat": "TRP-01",
        "desc_mat": "Pallet de madeira",
        "um": "CX",
        "fator_conv": 12,
        "qtd_ped": 10,
        "qtd_rec": 2,
        "preco_unit_centavos": 120000,
        "situacao": 1,
    },
    {
        "ped": "GL-778",
        "item": 2,
        "cnpj_fornecedor": "34567890000112",
        "nome_fornecedor": "Transportes Ideal ME",
        "dt_criacao": 1786752000,
        "cod_mat": "TRP-09",
        "desc_mat": "Caixa organizadora",
        "um": "CX",
        "fator_conv": 3,
        "qtd_ped": 4,
        "qtd_rec": 0,
        "preco_unit_centavos": 10000,
        "situacao": 1,
    },
    {
        "ped": "GL-779",
        "item": 1,
        "cnpj_fornecedor": "56789012000134",
        "nome_fornecedor": "Armazéns Rio Claro Ltda",
        "dt_criacao": 1784160000,
        "cod_mat": "ARM-10",
        "desc_mat": "Estrado metálico",
        "um": "UN",
        "fator_conv": 1,
        "qtd_ped": 100,
        "qtd_rec": 100,
        "preco_unit_centavos": 3500,
        "situacao": 2,
    },
]


@pytest.fixture
def ingested_client(client: TestClient) -> TestClient:
    resp = client.post("/ingestion/gama", json=GAMA_PAYLOAD)
    assert resp.status_code == 201
    return client


class TestIngestGama:
    def test_returns_summary_with_two_orders_three_items(self, client: TestClient):
        resp = client.post("/ingestion/gama", json=GAMA_PAYLOAD)
        assert resp.status_code == 201
        assert resp.json() == {"source_system": "gama", "orders_ingested": 2, "items_ingested": 3}


class TestListAndDetailGama:
    def test_filter_by_source_system_gama(self, ingested_client: TestClient):
        resp = ingested_client.get("/purchase-orders", params={"source_system": "gama"})
        assert resp.status_code == 200
        po_numbers = {o["po_number"] for o in resp.json()}
        assert po_numbers == {"GL-778", "GL-779"}

    def test_detail_shows_units_already_converted(self, ingested_client: TestClient):
        resp = ingested_client.get("/purchase-orders/gama/GL-778")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "open"

        item = next(i for i in body["items"] if i["material"] == "TRP-01")
        # 10 CX * fator_conv=12 -> 120 UN; a API nunca expõe "CX" nem fator_conv.
        assert item["uom"] == "UN"
        assert item["quantity_ordered"] == "120"
        assert item["quantity_received"] == "24"
        assert item["quantity_pending"] == "96"
        assert item["unit_price"] == "100"

    def test_detail_not_found_returns_404(self, ingested_client: TestClient):
        resp = ingested_client.get("/purchase-orders/gama/0000000")
        assert resp.status_code == 404


class TestInvoiceCheckAgainstGamaOrder:
    def test_compliant_check_using_unit_quantities(self, ingested_client: TestClient):
        # Nota fiscal sempre em unidades: 96 UN (== saldo pendente de 120-24) a R$100,00 cada.
        payload = {
            "source_system": "gama",
            "po_number": "GL-778",
            "vendor": {"tax_id": "34567890000112", "name": "Transportes Ideal ME"},
            "items": [{"material": "TRP-01", "quantity": 96, "total_value": 9600.00}],
        }
        resp = ingested_client.post("/invoice-checks", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "COMPLIANT"
        assert body["discrepancies"] == []

    def test_divergent_check_reports_vendor_mismatch(self, ingested_client: TestClient):
        payload = {
            "source_system": "gama",
            "po_number": "GL-779",
            "vendor": {"tax_id": "11111111000111", "name": "Fornecedor errado"},
            "items": [{"material": "ARM-10", "quantity": 100, "total_value": 3500.00}],
        }
        resp = ingested_client.post("/invoice-checks", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "DIVERGENT"
        assert body["discrepancies"][0]["type"] == "VENDOR_MISMATCH"
