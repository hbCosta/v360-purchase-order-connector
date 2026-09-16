import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage.purchase_order_repository import purchase_order_repository


@pytest.fixture(autouse=True)
def _reset_purchase_order_repository():
    """Isola os testes de API entre si — o repositório é um singleton em memória (design.md §11)."""
    purchase_order_repository.clear()
    yield
    purchase_order_repository.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
