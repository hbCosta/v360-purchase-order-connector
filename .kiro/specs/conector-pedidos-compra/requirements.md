# Requisitos — Conector de Pedidos de Compra V360

## 1. Contexto

A V360 recebe pedidos de compra (PO) de clientes diferentes (Alfa Energia, Beta Alimentos e,
futuramente, Gama Logística), cada um em um formato próprio. A aplicação a ser construída é uma
camada de integração que:

1. absorve essas diferenças de formato na fronteira (adapters por cliente);
2. normaliza os dados para um **modelo canônico único**;
3. expõe uma **API REST** consistente para consulta de pedidos;
4. **confere notas fiscais** recebidas da V360 contra os pedidos normalizados;
5. relata, de forma agregada, o resultado dessas conferências.

O domínio e a API nunca devem operar sobre os formatos originais dos clientes — apenas sobre o
modelo canônico.

## 2. Escopo

- **Parte 1**: clientes Alfa e Beta, modelo canônico, API de consulta, conferência de nota fiscal,
  relatório de conferências.
- **Parte 2**: adição do cliente Gama, incluindo a conversão de unidade de compra (`CX` +
  `fator_conv`) para unidade de estoque. A Parte 2 não deve exigir redesenho da Parte 1.

Marco de entrega: ao final da Parte 1 deve ser possível gerar uma tag `parte-1` com o sistema
funcional para Alfa + Beta, antes de qualquer código específico do Gama existir no repositório.

## 3. Glossário

| Termo | Significado |
|---|---|
| PO / Pedido de compra | Documento emitido pelo cliente representando uma intenção de compra, com um ou mais itens |
| Item do pedido | Linha do pedido, referenciando um material, quantidade e preço unitário |
| Situação (status) | Estado do pedido: aberto, fechado ou bloqueado, com vocabulário próprio por cliente |
| Saldo pendente | Quantidade ainda não recebida de um item (`quantidade_pedida - quantidade_recebida`) |
| Nota fiscal (invoice) | Documento enviado pela V360 para ser conferido contra um pedido já ingerido |
| Conferência | Operação que compara uma nota fiscal contra um pedido de compra e produz um resultado estruturado |
| Divergência | Diferença de **significado de negócio** encontrada durante uma conferência (não uma diferença de formatação) |
| `fator_conv` | Fator de conversão entre a unidade de compra (ex.: `CX`) e a unidade de estoque/unidades (Gama) |
| Modelo canônico | Representação única e neutra de pedido de compra, independente do cliente de origem |

## 4. Requisitos funcionais

### RF1 — Ingestão de pedidos Alfa

**RF1.1** O sistema deve aceitar um payload JSON no formato do Alfa (pedido com itens aninhados,
`po_number`, `created_at` em `YYYY-MM-DD`, status textual `open|closed|blocked`, fornecedor como
objeto) e convertê-lo para o modelo canônico.

```
DADO um payload JSON válido no formato Alfa
QUANDO ele for submetido ao endpoint de ingestão do Alfa
ENTÃO o pedido e seus itens devem ser armazenados no modelo canônico
E devem ficar disponíveis para consulta via API
```

### RF2 — Ingestão de pedidos Beta

**RF2.1** O sistema deve aceitar dois arquivos CSV separados por `;` (cabeçalho de pedidos e
itens de pedidos), relacioná-los por `NUMERO_PEDIDO`, e convertê-los para o modelo canônico.

```
DADO um CSV de cabeçalhos e um CSV de itens, relacionados por NUMERO_PEDIDO
QUANDO ambos forem submetidos ao endpoint de ingestão do Beta
ENTÃO cada pedido do cabeçalho deve ser combinado com seus itens correspondentes
E o resultado deve ser um pedido no modelo canônico
```

**RF2.2** Datas no formato `DD/MM/YYYY`, números no padrão brasileiro (`,` decimal) e CNPJ
formatado ou não devem ser normalizados corretamente.

### RF3 — Equivalência do modelo canônico

**RF3.1** Pedidos originados do Alfa e do Beta que representem a mesma informação de negócio
devem produzir a mesma estrutura de modelo canônico (mesmos campos, mesmos tipos, mesma semântica
de status, moeda e datas).

```
DADO um pedido do Alfa e um pedido do Beta com dados de negócio equivalentes
QUANDO ambos forem normalizados
ENTÃO os objetos resultantes devem ter os mesmos campos e tipos,
E nenhuma lógica de negócio deve precisar checar o cliente de origem para tratá-los
```

### RF4 — Consulta de pedidos

**RF4.1** Deve existir um endpoint para **listar** pedidos canônicos, com filtros por:
sistema de origem, fornecedor, situação e existência de saldo pendente.

**RF4.2** Deve existir um endpoint para **detalhar** um pedido específico, incluindo todos os
seus itens com quantidade pedida, recebida e pendente.

```
DADO que existem pedidos ingeridos de Alfa e Beta
QUANDO a API de listagem for chamada com filtro de situação = "aberto"
ENTÃO apenas pedidos com essa situação canônica devem ser retornados,
independentemente do vocabulário original do cliente
```

```
DADO um pedido existente identificado por sistema de origem + número do pedido
QUANDO o endpoint de detalhe for chamado
ENTÃO a resposta deve conter os itens do pedido com quantidade pedida, recebida e pendente
```

### RF5 — Conferência de nota fiscal

**RF5.1** A API deve receber dados de uma nota fiscal (fornecedor + itens, cada item com
material, quantidade e valor total) referenciando um pedido já ingerido, e retornar um resultado
estruturado da conferência.

**RF5.2** O resultado não deve ser um booleano simples: deve conter uma lista de divergências
estruturadas (podendo ser vazia) e um status geral (conforme/divergente).

```
DADO um pedido ingerido e conforme com uma nota fiscal cujos dados batem exatamente
QUANDO a nota for conferida
ENTÃO o resultado deve ter status "conforme" e lista de divergências vazia
```

```
DADO um pedido ingerido e uma nota fiscal com pelo menos uma diferença de negócio
QUANDO a nota for conferida
ENTÃO o resultado deve ter status "divergente"
E deve conter uma ou mais divergências estruturadas, cada uma explicando o motivo específico
```

**RF5.3** Tipos de divergência mínimos exigidos (lista pequena e extensível):

| Tipo | Quando ocorre |
|---|---|
| `VENDOR_MISMATCH` | CNPJ do fornecedor da nota difere do CNPJ do fornecedor do pedido (após normalização) |
| `MATERIAL_NOT_IN_ORDER` | Material informado na nota não existe em nenhum item do pedido |
| `QUANTITY_EXCEEDS_PENDING` | Quantidade da nota, para um material, é maior que o saldo pendente daquele material no pedido |
| `PRICE_MISMATCH` | Valor total da nota para um item não corresponde ao esperado (`quantidade × preço unitário do pedido`) |

**RF5.4** Diferenças de **representação** (máscara de CNPJ, separador decimal, formatação de
data) nunca devem gerar divergência — apenas diferenças de **significado de negócio**.

### RF6 — Relatório de conferências

**RF6.1** Deve existir um endpoint que agregue as conferências já realizadas, informando:
quantidade conforme, quantidade divergente, e contagem por tipo de divergência.

```
DADO um conjunto de conferências já realizadas, algumas conformes e outras divergentes
QUANDO o endpoint de relatório for chamado
ENTÃO a resposta deve informar o total de conferências, quantas foram conformes,
quantas foram divergentes, e a contagem de cada tipo de divergência observado
```

### RF7 — Ingestão do Gama (Parte 2)

**RF7.1** O sistema deve aceitar um payload JSON achatado do Gama (uma linha por item, dados do
pedido repetidos em cada linha), agrupar as linhas por `po_number` e convertê-las para o modelo
canônico.

**RF7.2** Datas em Unix timestamp (segundos), preço unitário em centavos e situação numérica
(`1|2|3`) devem ser normalizados para os mesmos tipos e vocabulário canônico usados por Alfa e
Beta.

**RF7.3** Quando a unidade do item for `CX`, quantidade pedida, quantidade recebida e preço
unitário devem ser convertidos para a unidade de estoque (unidades) usando `fator_conv`, de modo
que o pedido resultante já esteja na mesma unidade em que a nota fiscal sempre é emitida.

```
DADO um item do Gama com qtd_ped=10 CX, qtd_rec=2 CX, fator_conv=12
e preco_unit_centavos=120000 (preço da caixa)
QUANDO o pedido for normalizado
ENTÃO quantity_ordered canônico deve ser 120 unidades
E quantity_received canônico deve ser 24 unidades
E unit_price canônico deve ser R$ 100,00 por unidade (1200 / 12)
```

**RF7.4** A adição do Gama não deve exigir alteração nas regras de conferência, no contrato da
API de consulta, nem no formato de divergências definido na Parte 1.

## 5. Requisitos não funcionais

- **RNF1** — Stack: Python, FastAPI, Pydantic, `Decimal` para valores monetários, tipagem
  explícita (type hints em todas as assinaturas públicas), enums para conceitos fechados.
- **RNF2** — Número de dependências pequeno e justificável (ver `design.md`); evitar
  bibliotecas para problemas resolvíveis com a biblioteca padrão (ex.: parsing de CSV).
- **RNF3** — Nenhuma lógica de negócio ou de API deve conter condicionais por cliente de origem
  (`if source_system == "alfa"`); essas particularidades ficam restritas aos adapters.
- **RNF4** — O código deve ser explicável parte a parte durante uma avaliação técnica: preferir
  funções simples e diretas a abstrações genéricas não demandadas pelo problema.
- **RNF5** — Adicionar um novo cliente deve ser possível criando um novo adapter e registrando
  uma nova rota de ingestão, sem alterar `domain/` nem `services/` (exceto extensão pontual de
  enum, quando aplicável).

## 6. Regras de negócio explícitas

- **RN1** — Situação canônica é um conjunto fechado: `OPEN`, `CLOSED`, `BLOCKED`. Todo vocabulário
  de cliente deve ser mapeado para um desses três valores no adapter; um valor não mapeável deve
  causar erro de ingestão explícito, não um valor "desconhecido" silencioso.
- **RN2** — `quantidade_pendente` é **derivada**, nunca armazenada: `quantidade_pedida -
  quantidade_recebida`. Ver decisão registrada em `design.md`.
- **RN3** — A identidade de um pedido é o par `(sistema_de_origem, numero_do_pedido)`, nunca o
  número do pedido isoladamente (dois clientes podem usar a mesma numeração para pedidos
  diferentes).
- **RN4** — CNPJ é comparado sempre após normalização para uma forma canônica única (dígitos),
  nunca pela string original.
- **RN5** — A comparação de preço em uma conferência usa arredondamento apenas para eliminar
  ruído de representação decimal (2 casas, `ROUND_HALF_UP`), e não para introduzir tolerância de
  negócio. Qualquer diferença além disso é divergência. Ver ambiguidade A4 abaixo.
- **RN6** — Uma conferência de nota fiscal é uma operação de leitura: ela **não** altera a
  quantidade recebida do pedido armazenado. Ver ambiguidade A2 abaixo.
- **RN7** — Reingestão de um pedido já existente (mesma chave) substitui o pedido anterior
  (upsert), para permitir reprocessamento em um ambiente de demonstração.

## 7. Suposições assumidas

O desafio descreve o problema conceitualmente, sem anexar arquivos de exemplo reais. As
suposições abaixo foram necessárias para fechar o comportamento do sistema e estão documentadas
explicitamente, como pedido, em vez de assumidas silenciosamente:

- **S1** — Moeda é sempre `BRL`. O desafio não menciona múltiplas moedas; o campo `currency`
  existe no modelo canônico, mas nenhuma lógica de conversão é implementada.
- **S2** — Quando o cliente não informa quantidade recebida para um item, ela é considerada `0`.
- **S3** — Cada material aparece no máximo uma vez por pedido (uma linha por material). Repetição
  do mesmo material em múltiplas linhas do mesmo pedido é um caso não tratado explicitamente na
  Parte 1 (ver limitação conhecida em `design.md`).
- **S4** — A nota fiscal enviada para conferência referencia explicitamente o pedido que deve
  conferir, via `sistema_de_origem` + `numero_do_pedido` (a V360 já sabe contra qual pedido quer
  conferir, pois consultou a API de pedidos antes).
- **S5** — Alfa e Beta já informam quantidade e preço na mesma unidade usada pela nota fiscal
  (unidade de estoque); apenas o Gama introduz unidade de compra (`CX`) distinta da unidade de
  estoque.
- **S6** — Persistência é em memória, sem banco de dados (ver decisão em `design.md`). O escopo é
  um projeto demonstrativo de avaliação técnica, não um sistema produtivo.
- **S7** — As amostras do Beta mostram apenas `EM ABERTO` e `BLOQUEADO` para `SITUACAO`; o termo
  para pedido encerrado não aparece em nenhum exemplo. Assumido como `ENCERRADO` (termo padrão em
  português para o conceito), por analogia com `closed` do Alfa e `2 = encerrado` do Gama. Se o
  sistema real do Beta usar outro termo, é um ajuste de uma linha no mapa de vocabulário do
  adapter, sem impacto em nenhuma outra camada.
- **S8** — Nenhuma amostra usa vírgula como separador de milhar nem múltiplos formatos de UOM
  além de `UN`/`KG`/`CX`; a normalização de número tolera separador de milhar (`.`) e decimal
  (`,`) no padrão brasileiro, mas não tenta adivinhar outros padrões não observados.

## 8. Ambiguidades relevantes (destacadas, não resolvidas silenciosamente)

- **A1** — O desafio não define se pedidos com situação `CLOSED` ou `BLOCKED` podem ser
  conferidos normalmente. Decisão adotada: sim, a conferência não depende da situação do pedido,
  pois o desafio não pede essa restrição. Se a V360 quiser essa regra, é uma extensão pontual do
  `invoice_check_service`.
- **A2** — O desafio não define se múltiplas conferências sobre o mesmo pedido devem consumir o
  saldo pendente de forma acumulada (isto é, se a conferência funciona como um "recebimento").
  Decisão adotada (RN6): conferência é stateless — sempre compara contra o saldo pendente atual do
  pedido, sem acumular efeito de conferências anteriores. Esta é a ambiguidade de maior impacto
  arquitetural do desafio: se a regra real for "acumular recebimento", será necessário introduzir
  um conceito de histórico de recebimento que atualiza `quantidade_recebida` — uma evolução real do
  domínio, não apenas um ajuste de adapter.
- **A3** — Não há definição de o que fazer quando a nota fiscal referencia um pedido inexistente.
  Decisão adotada: HTTP 404, tratado como erro de pré-condição, não como divergência de negócio.
- **A4** — Não há tolerância numérica definida para preço. Decisão adotada (RN5): tolerância zero
  a nível de centavo, com arredondamento apenas para eliminar ruído de representação decimal.
- **A5** — Não é especificado se o desafio exige autenticação/autorização na API. Assumido fora de
  escopo, por não ser mencionado.

## 9. Anexo — exemplos reais de entrada (extraídos do enunciado)

Estes exemplos são a fonte de verdade para os schemas de entrada de cada adapter em
`design.md`.

### Alfa Energia (JSON)

```json
{
  "purchase_orders": [
    {
      "po_number": "4500001234",
      "created_at": "2026-08-05",
      "status": "open",
      "currency": "BRL",
      "vendor": { "tax_id": "23456789000101", "name": "Metalúrgica São Jorge S.A." },
      "items": [
        { "line": 10, "material": "MAT-1001", "description": "Chapa de aço 2mm",
          "uom": "UN", "quantity_ordered": 100, "quantity_received": 60, "unit_price": 45.9 },
        { "line": 20, "material": "MAT-1002", "description": "Perfil U 3m",
          "uom": "UN", "quantity_ordered": 50, "quantity_received": 0, "unit_price": 128.75 }
      ]
    }
  ]
}
```

`status` ∈ `{open, closed, blocked}`.

### Beta Alimentos (2 CSVs, `;`)

`cabecalho.csv`:
```
NUMERO_PEDIDO;FORNECEDOR_CNPJ;FORNECEDOR_RAZAO_SOCIAL;EMISSAO;SITUACAO;MOEDA
20260088412;12.345.678/0001-90;Distribuidora Horizonte Ltda;15/08/2026;EM ABERTO;BRL
20260088413;98.765.432/0001-55;Frigorífico Boa Mesa S.A.;01/08/2026;BLOQUEADO;BRL
```

`itens.csv`:
```
NUMERO_PEDIDO;ITEM;CODIGO_MATERIAL;DESCRICAO;UNIDADE;QTD_PEDIDA;QTD_RECEBIDA;PRECO_UNITARIO
20260088412;1;MAT-77;Óleo de soja 900ml;UN;1.200,000;400,000;6,49
20260088412;2;MAT-78;Açúcar refinado 1kg;UN;500,000;0,000;4,15
20260088413;1;MAT-91;Carne bovina dianteiro kg;KG;2.000,000;0,000;27,90
```

`SITUACAO` observado ∈ `{EM ABERTO, BLOQUEADO}` (ver suposição S7 para o termo de encerrado).

### Gama Logística (Parte 2 — JSON achatado)

```json
[
  { "ped": "GL-778", "item": 1, "cnpj_fornecedor": "34567890000112",
    "nome_fornecedor": "Transportes Ideal ME", "dt_criacao": 1786752000,
    "cod_mat": "TRP-01", "desc_mat": "Pallet de madeira", "um": "CX", "fator_conv": 12,
    "qtd_ped": 10, "qtd_rec": 2, "preco_unit_centavos": 120000, "situacao": 1 },
  { "ped": "GL-778", "item": 2, "cnpj_fornecedor": "34567890000112",
    "nome_fornecedor": "Transportes Ideal ME", "dt_criacao": 1786752000,
    "cod_mat": "TRP-09", "desc_mat": "Caixa organizadora", "um": "CX", "fator_conv": 3,
    "qtd_ped": 4, "qtd_rec": 0, "preco_unit_centavos": 10000, "situacao": 1 },
  { "ped": "GL-779", "item": 1, "cnpj_fornecedor": "56789012000134",
    "nome_fornecedor": "Armazéns Rio Claro Ltda", "dt_criacao": 1784160000,
    "cod_mat": "ARM-10", "desc_mat": "Estrado metálico", "um": "UN", "fator_conv": 1,
    "qtd_ped": 100, "qtd_rec": 100, "preco_unit_centavos": 3500, "situacao": 2 }
]
```

`situacao` ∈ `{1=open, 2=closed, 3=blocked}`. `preco_unit_centavos` é o preço **da unidade de
compra** (`um`), não da unidade de estoque — por isso a conversão por `fator_conv` deve recalcular
também o preço, não só a quantidade.

## 10. Fora de escopo

- Autenticação/autorização na API.
- Persistência durável (banco de dados) ou migrações.
- Suporte real a XML ou a um quarto cliente concreto (apenas o ponto de extensão é exigido).
- Qualquer comportamento específico de SAP/ERP não descrito no desafio.
- Conversão de moeda / suporte a múltiplas moedas.
- Fluxo de recebimento de mercadoria (atualização de `quantidade_recebida` via conferência).
