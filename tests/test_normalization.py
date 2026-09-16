from decimal import Decimal

import pytest

from app.normalization.dates import parse_br_date, parse_iso_date
from app.normalization.documents import normalize_tax_id
from app.normalization.money import parse_br_decimal, parse_decimal


class TestParseIsoDate:
    def test_alfa_sample(self):
        assert parse_iso_date("2026-08-05").isoformat() == "2026-08-05"


class TestParseBrDate:
    def test_beta_sample(self):
        assert parse_br_date("15/08/2026").isoformat() == "2026-08-15"

    def test_equivalent_to_iso_date_for_same_day(self):
        assert parse_iso_date("2026-08-05") == parse_br_date("05/08/2026")


class TestParseDecimal:
    def test_int(self):
        assert parse_decimal(100) == Decimal("100")

    def test_float_avoids_binary_representation_error(self):
        # Decimal(45.9) direto herdaria o erro binario do float; parse_decimal nao.
        assert parse_decimal(45.9) == Decimal("45.9")
        assert Decimal(45.9) != Decimal("45.9")

    def test_str(self):
        assert parse_decimal("128.75") == Decimal("128.75")

    def test_decimal_passthrough(self):
        value = Decimal("10.5")
        assert parse_decimal(value) is value


class TestParseBrDecimal:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("1.200,000", "1200.000"),
            ("500,000", "500.000"),
            ("6,49", "6.49"),
            ("4,15", "4.15"),
            ("2.000,000", "2000.000"),
            ("27,90", "27.90"),
        ],
    )
    def test_beta_samples(self, raw: str, expected: str):
        assert parse_br_decimal(raw) == Decimal(expected)


class TestNormalizeTaxId:
    def test_removes_mask(self):
        assert normalize_tax_id("12.345.678/0001-90") == "12345678000190"

    def test_masked_and_unmasked_are_equal(self):
        assert normalize_tax_id("12.345.678/0001-90") == normalize_tax_id("12345678000190")

    def test_idempotent(self):
        normalized = normalize_tax_id("98.765.432/0001-55")
        assert normalize_tax_id(normalized) == normalized
