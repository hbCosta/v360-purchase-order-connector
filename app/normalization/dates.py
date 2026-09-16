from datetime import date, datetime, timezone


def parse_iso_date(value: str) -> date:
    """Converte uma data no formato ISO `YYYY-MM-DD` (Alfa) para `date`."""
    return date.fromisoformat(value)


def parse_br_date(value: str) -> date:
    """Converte uma data no formato brasileiro `DD/MM/YYYY` (Beta) para `date`."""
    return datetime.strptime(value, "%d/%m/%Y").date()


def parse_unix_timestamp(value: int) -> date:
    """Converte um timestamp Unix em segundos (Gama) para `date`.

    Usa UTC explicitamente — evita que o resultado dependa do fuso horário configurado na
    máquina onde a aplicação roda (o timestamp já representa um instante absoluto).
    """
    return datetime.fromtimestamp(value, tz=timezone.utc).date()
