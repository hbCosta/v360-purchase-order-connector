# Tasks — Conector de Pedidos de Compra V360

Cada tarefa depende apenas de tarefas anteriores e referencia o requisito (`RFx`/`RNx`) e a
seção de `design.md` que implementa. O repositório está vazio — a Parte 1 começa do zero.

## Parte 1 — Alfa + Beta

### Bootstrap

**T01 — Estrutura inicial do repositório** ✅ Concluída
Criar a árvore de diretórios descrita em `design.md` §2 (`app/` com todos os subpacotes vazios,
cada um com `__init__.py`), `.gitignore` (venv, `__pycache__`, `.pytest_cache`), e inicializar o
repositório git (`git init`, primeiro commit).
*Depende de*: nada.

**T02 — Configuração do projeto Python** ✅ Concluída
Criar `pyproject.toml` (ou `requirements.txt` + `requirements-dev.txt`) com as dependências de
`design.md` §12: `fastapi`, `uvicorn`, `pydantic`, `python-multipart`, e dev: `pytest`, `httpx`.
Documentar como criar o ambiente virtual e instalar dependências.
*Depende de*: T01. *Atende*: RNF2.

**T03 — Aplicação FastAPI mínima** ✅ Concluída
Criar `app/main.py` instanciando o FastAPI app e um endpoint `GET /health` retornando `{"status":
"ok"}`. Confirmar que `uvicorn app.main:app --reload` sobe.
*Depende de*: T02.

### Domínio

**T04 — Enums do domínio** ✅ Concluída
Criar `app/domain/enums.py` com `SourceSystem` (`ALFA`, `BETA` — sem `GAMA` ainda),
`OrderStatus` (`OPEN`, `CLOSED`, `BLOCKED`), `DivergenceType` (`VENDOR_MISMATCH`,
`MATERIAL_NOT_IN_ORDER`, `QUANTITY_EXCEEDS_PENDING`, `PRICE_MISMATCH`), `CheckStatus`
(`COMPLIANT`, `DIVERGENT`).
*Depende de*: T03. *Atende*: RN1, RF5.3.

**T05 — Modelo canônico** ✅ Concluída
Criar `app/domain/models.py` com `Vendor`, `PurchaseOrderItem` (com propriedade
`quantity_pending`) e `PurchaseOrder` (com propriedade `id`), usando `Decimal` para todo campo
monetário/quantidade, conforme `design.md` §3.
*Depende de*: T04. *Atende*: RN2, RN3, decisão D5/D6.

**T06 — Modelos de conferência** ✅ Concluída
Criar `app/domain/invoice.py` (`Invoice`, `InvoiceItem` — entrada de uma conferência) e
`app/domain/discrepancies.py` (`Discrepancy`, `InvoiceCheckResult`), conforme `design.md` §7.
*Depende de*: T05.

**T07 — Exceções de domínio** ✅ Concluída
Criar `app/domain/exceptions.py` com `PurchaseOrderNotFoundError` e uma exceção de parsing
(`AdapterParsingError`) usada quando um adapter encontra um valor fora do vocabulário esperado
(RN1).
*Depende de*: T05.

### Normalização (utilitários de formato)

**T08 — Normalização de datas** ✅ Concluída
Criar `app/normalization/dates.py` com `parse_iso_date` e `parse_br_date`. (`parse_unix_timestamp`
entra só na T22, Parte 2, mas o arquivo já existe aqui.)
*Depende de*: T03. *Atende*: RF1, RF2.2.

**T09 — Normalização monetária** ✅ Concluída
Criar `app/normalization/money.py` com `parse_decimal` (aceita `int`/`float`/`str` sem passar por
`float` internamente) e `parse_br_decimal` (trata separador de milhar `.` e decimal `,`).
*Depende de*: T03. *Atende*: RN da §5.2 de `design.md`.

**T10 — Normalização de CNPJ** ✅ Concluída
Criar `app/normalization/documents.py` com `normalize_tax_id` (remove `.`, `/`, `-`).
*Depende de*: T03. *Atende*: RN4.

**T11 — Testes de normalização** ✅ Concluída
Testes unitários para T08–T10 cobrindo os exemplos reais do enunciado (`requirements.md` §9):
`"2026-08-05"`, `"15/08/2026"`, `"1.200,000"`, `"6,49"`, `"12.345.678/0001-90"`.
*Depende de*: T08, T09, T10.

### Repositório em memória

**T12 — Repositório de pedidos** ✅ Concluída
Criar `app/storage/purchase_order_repository.py`: `upsert(order)`, `get(source_system,
po_number)`, `list(source_system=None, vendor_tax_id=None, status=None, has_pending=None)`.
*Depende de*: T05. *Atende*: RF4, RN7, decisão D11.

### Adapter Alfa

**T13 — Schemas brutos do Alfa** ✅ Concluída
Criar `app/integrations/alfa/schemas.py` com os modelos Pydantic do payload bruto (baseado no
exemplo de `requirements.md` §9: `purchase_orders[]`, `vendor{tax_id,name}`, `items[]`).
*Depende de*: T03.

**T14 — Adapter Alfa** ✅ Concluída
Criar `app/integrations/alfa/adapter.py::parse_orders(payload) -> list[PurchaseOrder]`, com o mapa
de status `{open, closed, blocked}` e uso dos normalizadores de T08–T10.
*Depende de*: T05, T07, T08, T09, T10, T13. *Atende*: RF1.

**T15 — Testes do adapter Alfa** ✅ Concluída
Teste com o payload de exemplo do enunciado; validar que o `PurchaseOrder` resultante bate campo a
campo com o esperado; validar que um `status` desconhecido levanta `AdapterParsingError`.
*Depende de*: T14.

### Adapter Beta

**T16 — Schemas brutos do Beta** ✅ Concluída
Criar `app/integrations/beta/schemas.py` com `BetaHeaderRow` e `BetaItemRow` espelhando as colunas
de `cabecalho.csv` e `itens.csv` (`requirements.md` §9).
*Depende de*: T03.

**T17 — Adapter Beta** ✅ Concluída
Criar `app/integrations/beta/adapter.py::parse_orders(header_csv_text, items_csv_text) ->
list[PurchaseOrder]`: parsing com `csv.DictReader(delimiter=";")`, agrupamento por
`NUMERO_PEDIDO`, mapa de status `{EM ABERTO, ENCERRADO, BLOQUEADO}` (suposição S7 documentada no
código), uso dos normalizadores de T08–T10.
*Depende de*: T05, T07, T08, T09, T10, T16. *Atende*: RF2.

**T18 — Testes do adapter Beta** ✅ Concluída
Teste com os dois CSVs de exemplo do enunciado; validar agrupamento correto por `NUMERO_PEDIDO`;
validar erro explícito quando um item referencia um pedido sem cabeçalho.
*Depende de*: T17.

### Equivalência canônica

**T19 — Teste de equivalência Alfa vs. Beta** ✅ Concluída
Teste que constrói, a partir de dados equivalentes em ambos os formatos, dois `PurchaseOrder` e
verifica que a única diferença é `source_system`/`po_number` — todos os demais campos têm mesmo
tipo e semântica (RF3.1).
*Depende de*: T15, T18.

### Ingestão e consulta

**T20 — Router de ingestão (Alfa + Beta)** ✅ Concluída
Criar `app/api/routers/ingestion.py`: `POST /ingestion/alfa` (body JSON) e `POST /ingestion/beta`
(multipart com dois arquivos), cada um chamando o adapter correspondente e fazendo `upsert` no
repositório; resposta com resumo (pedidos/itens ingeridos).
*Depende de*: T12, T14, T17. *Atende*: RF1, RF2.

**T21 — Service de consulta de pedidos** ✅ Concluída
Criar `app/services/purchase_order_service.py` com `list_orders(...)` e `get_order(...)` sobre o
repositório, conforme `design.md` §6.
*Depende de*: T12.

**T22 — Schemas de resposta de pedidos** ✅ Concluída
Criar `app/api/schemas/purchase_order.py` (DTOs de listagem e detalhe, incluindo
`quantity_pending` calculado por item).
*Depende de*: T05.

**T23 — Router de consulta de pedidos** ✅ Concluída
Criar `app/api/routers/purchase_orders.py`: `GET /purchase-orders` (filtros de RF4.1) e `GET
/purchase-orders/{source_system}/{po_number}` (detalhe, 404 se não existir).
*Depende de*: T21, T22. *Atende*: RF4.

**T24 — Testes de API de ingestão + consulta** ✅ Concluída
Testes end-to-end com `TestClient`: ingerir Alfa e Beta, depois listar com cada filtro e buscar o
detalhe de um pedido específico.
*Depende de*: T20, T23.

### Conferência de nota fiscal

**T25 — Schemas de request/response de conferência** ✅ Concluída
Criar `app/api/schemas/invoice_check.py` (request de `POST /invoice-checks` e response com
`status` + `discrepancies[]`), conforme exemplo de `design.md` §8.
*Depende de*: T06.

**T26 — Service de conferência** ✅ Concluída
Criar `app/services/invoice_check_service.py::check(order, invoice) -> InvoiceCheckResult`
implementando o algoritmo completo de `design.md` §6 (fornecedor, material, quantidade
pendente, preço), sempre retornando todas as divergências encontradas.
*Depende de*: T06, T09, T10. *Atende*: RF5, RN5, RN6.

**T27 — Testes do service de conferência** ✅ Concluída
Um teste por cenário: conforme; `VENDOR_MISMATCH`; `MATERIAL_NOT_IN_ORDER`;
`QUANTITY_EXCEEDS_PENDING`; `PRICE_MISMATCH`; múltiplas divergências simultâneas no mesmo
resultado.
*Depende de*: T26.

**T28 — Repositório de conferências** ✅ Concluída
Criar `app/storage/invoice_check_repository.py`: `append(result)`, `list(...)`.
*Depende de*: T06.

**T29 — Router de conferência** ✅ Concluída
Criar `app/api/routers/invoice_checks.py`: `POST /invoice-checks` (busca o pedido, chama o
service, persiste o resultado, 404 se pedido não existir) e `GET /invoice-checks` (histórico).
*Depende de*: T25, T26, T28. *Atende*: RF5, A3.

**T30 — Testes de API de conferência** ✅ Concluída
Testes end-to-end: conferir nota conforme e divergente contra um pedido ingerido via API; conferir
contra pedido inexistente (404).
*Depende de*: T29.

### Relatório

**T31 — Service de relatório** ✅ Concluída
Criar `app/services/report_service.py::summarize() -> ReportSummary` (total, conformes,
divergentes, contagem por `DivergenceType`), conforme `design.md` §6.
*Depende de*: T28.

**T32 — Router de relatório** ✅ Concluída
Criar `app/api/routers/reports.py`: `GET /reports/invoice-checks`.
*Depende de*: T31. *Atende*: RF6.

**T33 — Testes de relatório** ✅ Concluída
Teste end-to-end: realizar múltiplas conferências (conformes e divergentes de tipos diferentes) e
validar a agregação retornada.
*Depende de*: T32.

### Documentação e fechamento da Parte 1

**T34 — README** ✅ Concluída
Escrever `README.md`: como rodar (venv, instalar, `uvicorn`), como ingerir dados de exemplo (curl
para Alfa/Beta), como consultar pedidos, como conferir uma nota, como ver o relatório; seção
"Decisões de negócio assumidas" resumindo as suposições/ambiguidades de `requirements.md` §7–8 em
linguagem direta (a dica do próprio enunciado pede exatamente isso).
*Depende de*: T33.

**T35 — Fixtures de exemplo** ✅ Concluída
Criar `examples/alfa_payload.json`, `examples/beta_cabecalho.csv`, `examples/beta_itens.csv` com
os dados de amostra do enunciado, prontos para uso no README e em uma demo ao vivo.
*Depende de*: T34.

**T36 — Revisão final da Parte 1** ✅ Concluída
Rodar toda a suíte de testes; conferir manualmente, via Swagger (`/docs`), os três fluxos (ingestão
→ consulta → conferência → relatório) usando as fixtures de T35; checklist contra RF1–RF6 de
`requirements.md`.
*Depende de*: T35.

---

## MARCO — fim da Parte 1

**T37 — Commit e tag `parte-1`** ✅ Concluída
Commitar o estado final da Parte 1 e criar `git tag parte-1`. Nenhum arquivo de
`integrations/gama/` deve existir neste ponto.
*Depende de*: T36.

---

## Parte 2 — Gama Logística

**T38 — Adicionar `GAMA` ao enum `SourceSystem`** ✅ Concluída
Editar `app/domain/enums.py` — único ponto de edição fora de `integrations/` nesta parte (ver
`design.md` §10).
*Depende de*: T37. *Atende*: RF7.

**T39 — Schemas brutos do Gama** ✅ Concluída
Criar `app/integrations/gama/schemas.py` com `GamaItemRow` espelhando o JSON achatado
(`requirements.md` §9).
*Depende de*: T38.

**T40 — Normalização de timestamp Unix** ✅ Concluída
Adicionar `parse_unix_timestamp` a `app/normalization/dates.py` (arquivo já existe desde T08).
*Depende de*: T38. *Atende*: RF7.2.

**T41 — Adapter Gama: agrupamento e mapeamento direto** ✅ Concluída
Criar `app/integrations/gama/adapter.py::parse_orders(payload) -> list[PurchaseOrder]`:
agrupamento por `ped`, mapa de situação `{1: OPEN, 2: CLOSED, 3: BLOCKED}`, uso de
`parse_unix_timestamp`, `cents_to_decimal` e `normalize_tax_id`. Sem conversão de unidade ainda
(assume `um == "UN"`).
*Depende de*: T39, T40.

**T42 — Conversão de unidade de compra (`CX` + `fator_conv`)** ✅ Concluída
Estender `app/integrations/gama/adapter.py` para aplicar a conversão descrita em `design.md` §4.4
quando `um == "CX"`: `quantity_ordered`, `quantity_received` e `unit_price` recalculados; `uom`
canônico vira `"UN"`.
*Depende de*: T41. *Atende*: RF7.3.

**T43 — Testes do adapter Gama** ✅ Concluída
Testes com os três itens de exemplo do enunciado (`GL-778` item 1 e 2, `GL-779` item 1),
verificando: agrupamento correto em 2 pedidos; conversão `10 CX × fator_conv=12 → 120 unidades` e
preço `R$100,00/unidade`; item já em `UN` (`fator_conv=1`) passa sem alteração de valor.
*Depende de*: T42.

**T44 — Router de ingestão: adicionar Gama** ✅ Concluída
Adicionar `POST /ingestion/gama` a `app/api/routers/ingestion.py` — mudança aditiva (nova rota),
sem tocar nas rotas de Alfa/Beta.
*Depende de*: T42. *Atende*: RF7.1.

**T45 — Teste de não regressão nas regras centrais** ✅ Concluída
Confirmar, com teste explícito, que `invoice_check_service`, `purchase_order_service` e
`report_service` não foram alterados nesta parte (nenhum diff nesses arquivos) e que uma
conferência de nota fiscal contra um pedido do Gama passa pelo mesmo `check(...)` usado por
Alfa/Beta, sem nenhum código condicional por cliente.
*Depende de*: T44.

**T46 — Testes de API end-to-end com Gama** ✅ Concluída
Ingerir o payload de exemplo do Gama via API; listar pedidos filtrando `source_system=gama`;
detalhar um pedido do Gama; conferir uma nota fiscal (quantidade em unidades) contra ele.
*Depende de*: T45.

**T47 — Atualizar README com o impacto real da Parte 2** ✅ Concluída
Seção nova no `README.md`: lista exata dos arquivos tocados (`design.md` §10) confirmando o que
foi só adicionado (`integrations/gama/*`, rota nova) e o que exigiu tocar em código existente
(uma linha em `SourceSystem`) — respondendo diretamente à pergunta do enunciado sobre o que mudou
para o Gama entrar.
*Depende de*: T46.

**T48 — Commit e tag `parte-2`** ✅ Concluída
Commitar o estado final e criar `git tag parte-2`.
*Depende de*: T47.
