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


def _check(client: TestClient, vendor_tax_id: str, material: str, quantity: float, total: float):
    return client.post(
        "/invoice-checks",
        json={
            "source_system": "alfa",
            "po_number": "4500001234",
            "vendor": {"tax_id": vendor_tax_id, "name": "Fornecedor X"},
            "items": [{"material": material, "quantity": quantity, "total_value": total}],
        },
    )


class TestInvoiceChecksReport:
    def test_report_is_empty_before_any_check(self, ingested_client: TestClient):
        resp = ingested_client.get("/reports/invoice-checks")
        assert resp.status_code == 200
        assert resp.json() == {
            "total": 0,
            "compliant_count": 0,
            "divergent_count": 0,
            "discrepancy_type_counts": {},
        }

    def test_report_aggregates_compliant_and_divergent_by_type(self, ingested_client: TestClient):
        # 2 conformes (10 * 45.9 = 459.00)
        _check(ingested_client, "23456789000101", "MAT-1001", 10, 459.00)
        _check(ingested_client, "23456789000101", "MAT-1001", 10, 459.00)
        # material inexistente
        _check(ingested_client, "23456789000101", "MAT-XXXX", 1, 1.00)
        # fornecedor errado + preço incompatível (5 * 45.9 = 229.50 != 1.00) na mesma conferência
        _check(ingested_client, "11111111000111", "MAT-1001", 5, 1.00)

        resp = ingested_client.get("/reports/invoice-checks")
        assert resp.status_code == 200
        body = resp.json()

        assert body["total"] == 4
        assert body["compliant_count"] == 2
        assert body["divergent_count"] == 2
        assert body["discrepancy_type_counts"] == {
            "MATERIAL_NOT_IN_ORDER": 1,
            "VENDOR_MISMATCH": 1,
            "PRICE_MISMATCH": 1,
        }

    def test_report_reflects_only_checks_performed_against_existing_orders(
        self, ingested_client: TestClient
    ):
        # nao deve contar: pedido inexistente da 404 e nunca e persistido
        ingested_client.post(
            "/invoice-checks",
            json={
                "source_system": "alfa",
                "po_number": "9999999",
                "vendor": {"tax_id": "23456789000101", "name": "Fornecedor X"},
                "items": [{"material": "MAT-1001", "quantity": 1, "total_value": 45.9}],
            },
        )
        resp = ingested_client.get("/reports/invoice-checks")
        assert resp.json()["total"] == 0
