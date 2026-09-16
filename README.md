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

## Rodando com Docker

Alternativa ao passo de instalação acima — não precisa de Python nem venv instalados, só Docker.

**1. Construir a imagem:**
```bash
docker build -t v360-po-connector .
```

**2. Executar o container:**
```bash
docker run -d --name v360-po-connector -p 8000:8000 v360-po-connector
```

**3. Acessar a API:**

`http://localhost:8000` — documentação interativa (Swagger) em `http://localhost:8000/docs`.

**4. Encerrar o container:**
```bash
docker stop v360-po-connector
docker rm v360-po-connector
```

A imagem instala só as dependências de runtime (`requirements.txt`); testes rodam fora do
container, no ambiente local (seção "Testes" acima).
