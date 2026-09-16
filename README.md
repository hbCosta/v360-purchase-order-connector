# Conector de Pedidos de Compra V360

Camada de integração que normaliza pedidos de compra de diferentes clientes (Alfa Energia, Beta
Alimentos e, futuramente, Gama Logística) para um modelo canônico único, expondo uma API REST de
consulta, conferência de nota fiscal e relatório de conferências.

A especificação completa (requisitos, design e plano de implementação) está em
[`.kiro/specs/conector-pedidos-compra/`](.kiro/specs/conector-pedidos-compra/).

## Instalação

Requer Python 3.11+.

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

**Linux/macOS:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

`requirements-dev.txt` inclui `requirements.txt` (dependências de runtime) mais `pytest`/`httpx`
para os testes.

## Rodando a aplicação

```bash
uvicorn app.main:app --reload
```

A API fica disponível em `http://127.0.0.1:8000`, com documentação interativa em
`http://127.0.0.1:8000/docs`.

## Testes

```bash
pytest
```
