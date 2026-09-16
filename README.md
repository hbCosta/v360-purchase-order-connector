# Conector de Pedidos de Compra V360

Camada de integração que normaliza pedidos de compra de diferentes clientes (Alfa Energia, Beta
Alimentos e, futuramente, Gama Logística) para um modelo canônico único, expondo uma API REST de
consulta, conferência de nota fiscal e relatório de conferências.

A especificação completa (requisitos, design e plano de implementação) está em
[`.kiro/specs/conector-pedidos-compra/`](.kiro/specs/conector-pedidos-compra/).

## Índice

- [Tecnologias](#tecnologias)
- [Como rodar o projeto](#como-rodar-o-projeto)
- [Exemplos de uso](#exemplos-de-uso)
- [Decisões que tomei](#decisões-que-tomei)
- [O que eu faria diferente com mais tempo](#o-que-eu-faria-diferente-com-mais-tempo)

## Tecnologias

- **Python 3.13** com tipagem explícita
- **FastAPI** + **Pydantic v2** — API REST e validação/serialização
- **`Decimal`** para todo valor monetário e de quantidade (nunca `float`)
- **pytest** — suíte de testes automatizados
- **Docker** — execução sem precisar instalar Python localmente

Sem banco de dados, ORM, fila ou biblioteca de CSV: dependências mínimas e justificadas (detalhe
em `design.md`, seção 15).

## Como rodar o projeto

Duas formas equivalentes — escolha uma.

### Opção A — local (Python)

Requer Python 3.11+.

**1. Criar e ativar o ambiente virtual:**

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux/macOS:
```bash
python -m venv .venv
source .venv/bin/activate
```

**2. Instalar as dependências:**
```bash
pip install -r requirements-dev.txt
```
(inclui `requirements.txt`, de runtime, mais `pytest`/`httpx` para os testes)

**3. Rodar a aplicação:**
```bash
uvicorn app.main:app --reload
```

**4. Acessar:** `http://127.0.0.1:8000` — documentação interativa em `http://127.0.0.1:8000/docs`.

**Rodar os testes:**
```bash
pytest
```

### Opção B — Docker

Não precisa de Python nem venv instalados, só Docker.

**1. Construir a imagem:**
```bash
docker build -t v360-po-connector .
```

**2. Executar o container:**
```bash
docker run -d --name v360-po-connector -p 8000:8000 v360-po-connector
```

**3. Acessar:** `http://localhost:8000` — documentação em `http://localhost:8000/docs`.

**4. Encerrar:**
```bash
docker stop v360-po-connector
docker rm v360-po-connector
```

A imagem instala só as dependências de runtime; os testes rodam fora do container, na Opção A.

## Exemplos de uso

Com a aplicação rodando (Opção A ou B) em `http://127.0.0.1:8000`. Os arquivos de exemplo ficam
em [`examples/`](examples/) — os mesmos dados de amostra do enunciado do desafio.

**1. Ingerir pedidos do Alfa (JSON):**
```bash
curl -X POST http://127.0.0.1:8000/ingestion/alfa \
  -H "Content-Type: application/json" \
  --data-binary @examples/alfa_payload.json
```

**2. Ingerir pedidos do Beta (dois CSVs):**
```bash
curl -X POST http://127.0.0.1:8000/ingestion/beta \
  -F "cabecalho=@examples/beta_cabecalho.csv;type=text/csv" \
  -F "itens=@examples/beta_itens.csv;type=text/csv"
```

**3. Consultar pedidos:**
```bash
curl http://127.0.0.1:8000/purchase-orders
curl "http://127.0.0.1:8000/purchase-orders?source_system=alfa&has_pending=true"
curl http://127.0.0.1:8000/purchase-orders/alfa/4500001234
```

**4. Conferir uma nota fiscal contra um pedido:**
```bash
curl -X POST http://127.0.0.1:8000/invoice-checks \
  -H "Content-Type: application/json" \
  -d '{
    "source_system": "alfa",
    "po_number": "4500001234",
    "vendor": { "tax_id": "23456789000101", "name": "Metalúrgica São Jorge S.A." },
    "items": [ { "material": "MAT-1001", "quantity": 40, "total_value": 1836.00 } ]
  }'
```
A resposta traz `status` (`COMPLIANT`/`DIVERGENT`) e, se divergente, a lista de `discrepancies`
estruturadas (`type`, `material`, `message`, `expected`, `actual`).

**5. Ver o relatório de conferências:**
```bash
curl http://127.0.0.1:8000/reports/invoice-checks
```

Todos os endpoints também podem ser explorados interativamente em `/docs` (Swagger UI).

## Decisões que tomei

### Arquitetura

Resumo — o raciocínio completo, com alternativa considerada e trade-off para cada uma, está em
`.kiro/specs/conector-pedidos-compra/design.md` (seção 14):

- **Um adapter por cliente** (`integrations/alfa`, `integrations/beta`), cada um absorvendo 100%
  das particularidades daquele formato (campos, datas, números, vocabulário de situação). Nenhuma
  lógica de negócio conhece o cliente de origem — só o adapter.
- **Modelo canônico único**, sem herança por cliente, para que domínio/serviços/API operem sobre
  uma única representação.
- **`Decimal` em todo valor monetário/quantidade**, nunca `float` — evita erro de representação
  binária ao comparar preço da nota contra o pedido.
- **`quantity_pending` é calculada, nunca armazenada** (`quantity_ordered - quantity_received`) —
  elimina o risco de duas fontes de verdade ficarem dessincronizadas.
- **Identidade do pedido é o par `(source_system, po_number)`**, nunca o número isolado, já que
  clientes diferentes podem reaproveitar numeração.
- **Divergência com formato genérico** (`type/material/message/expected/actual`) em vez de uma
  classe por tipo — adicionar um tipo novo não exige nova classe nem migração de schema.
- **Persistência em memória**, sem banco — adequado ao escopo de demonstração técnica, não a um
  ambiente produtivo (ver "o que eu faria diferente" abaixo).


## O que eu faria diferente com mais tempo

- **Validar a ambiguidade de maior risco com o time de negócio antes de tudo**: se a conferência
  deveria consumir o saldo pendente (funcionar como um recebimento) em vez de ser stateless — é a
  decisão que mais mudaria a arquitetura do domínio.
- **Persistência real** (Postgres, por exemplo) no lugar do repositório em memória, com migração
  de schema — hoje os dados somem a cada restart.
- **Autenticação/autorização na API**, já que qualquer um com acesso à rede pode ingerir dados ou
  consultar pedidos.
- **Observabilidade**: logging estruturado e métricas básicas (conferências por minuto, latência
  por endpoint) — hoje só existe o log padrão do Uvicorn.
