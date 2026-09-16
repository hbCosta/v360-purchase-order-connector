import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage.invoice_check_repository import invoice_check_repository
from app.storage.purchase_order_repository import purchase_order_repository


@pytest.fixture(autouse=True)
def _reset_repositories():
    """Isola os testes de API entre si — os repositórios são singletons em memória (design.md §11)."""
    purchase_order_repository.clear()
    invoice_check_repository.clear()
    yield
    purchase_order_repository.clear()
    invoice_check_repository.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
