from datetime import date, datetime


def parse_iso_date(value: str) -> date:
    """Converte uma data no formato ISO `YYYY-MM-DD` (Alfa) para `date`."""
    return date.fromisoformat(value)


def parse_br_date(value: str) -> date:
    """Converte uma data no formato brasileiro `DD/MM/YYYY` (Beta) para `date`."""
    return datetime.strptime(value, "%d/%m/%Y").date()
