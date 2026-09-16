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


@pytest.fixture
def ingested_client(client: TestClient) -> TestClient:
    resp = client.post("/ingestion/alfa", json=ALFA_PAYLOAD)
    assert resp.status_code == 201
    return client


class TestCreateInvoiceCheck:
    def test_compliant_invoice_returns_200_with_no_discrepancies(
        self, ingested_client: TestClient
    ):
        payload = {
            "source_system": "alfa",
            "po_number": "4500001234",
            "vendor": {"tax_id": "23.456.789/0001-01", "name": "Metalúrgica São Jorge S.A."},
            "items": [{"material": "MAT-1001", "quantity": 40, "total_value": 1836.00}],
        }
        resp = ingested_client.post("/invoice-checks", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "COMPLIANT"
        assert body["discrepancies"] == []

    def test_divergent_invoice_returns_200_with_structured_discrepancies(
        self, ingested_client: TestClient
    ):
        payload = {
            "source_system": "alfa",
            "po_number": "4500001234",
            "vendor": {"tax_id": "23456789000101", "name": "Metalúrgica São Jorge S.A."},
            "items": [{"material": "MAT-9999", "quantity": 5, "total_value": 100.00}],
        }
        resp = ingested_client.post("/invoice-checks", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "DIVERGENT"
        assert len(body["discrepancies"]) == 1
        assert body["discrepancies"][0]["type"] == "MATERIAL_NOT_IN_ORDER"
        assert body["discrepancies"][0]["material"] == "MAT-9999"

    def test_invoice_check_against_unknown_order_returns_404(self, ingested_client: TestClient):
        payload = {
            "source_system": "alfa",
            "po_number": "9999999",
            "vendor": {"tax_id": "23456789000101", "name": "Metalúrgica São Jorge S.A."},
            "items": [{"material": "MAT-1001", "quantity": 1, "total_value": 45.9}],
        }
        resp = ingested_client.post("/invoice-checks", json=payload)
        assert resp.status_code == 404


class TestListInvoiceChecks:
    def test_empty_history_before_any_check(self, ingested_client: TestClient):
        resp = ingested_client.get("/invoice-checks")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_history_accumulates_performed_checks(self, ingested_client: TestClient):
        compliant_payload = {
            "source_system": "alfa",
            "po_number": "4500001234",
            "vendor": {"tax_id": "23456789000101", "name": "Metalúrgica São Jorge S.A."},
            "items": [{"material": "MAT-1001", "quantity": 40, "total_value": 1836.00}],
        }
        divergent_payload = {
            "source_system": "alfa",
            "po_number": "4500001234",
            "vendor": {"tax_id": "23456789000101", "name": "Metalúrgica São Jorge S.A."},
            "items": [{"material": "MAT-9999", "quantity": 5, "total_value": 100.00}],
        }
        ingested_client.post("/invoice-checks", json=compliant_payload)
        ingested_client.post("/invoice-checks", json=divergent_payload)

        resp = ingested_client.get("/invoice-checks")
        assert resp.status_code == 200
        statuses = [entry["status"] for entry in resp.json()]
        assert statuses == ["COMPLIANT", "DIVERGENT"]

    def test_check_against_unknown_order_is_not_persisted(self, ingested_client: TestClient):
        payload = {
            "source_system": "alfa",
            "po_number": "9999999",
            "vendor": {"tax_id": "23456789000101", "name": "Metalúrgica São Jorge S.A."},
            "items": [{"material": "MAT-1001", "quantity": 1, "total_value": 45.9}],
        }
        ingested_client.post("/invoice-checks", json=payload)  # 404, não deve persistir

        resp = ingested_client.get("/invoice-checks")
        assert resp.json() == []
