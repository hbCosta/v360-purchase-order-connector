# Uso de IA neste projeto

## Quais ferramentas usei e em quais partes

Usei o **Claude Code** (modelo Claude Sonnet 5, da Anthropic) em
todas as etapas:

- **Planejamento** — antes de escrever qualquer código, pedi um processo de spec-driven
  development: `requirements.md` (requisitos rastreáveis, com critérios de aceitação),
  `design.md` (arquitetura, decisões com alternativa/trade-off) e `tasks.md` (plano de
  implementação em tarefas pequenas e ordenadas). Esses três documentos estão versionados em
  [`.kiro/specs/conector-pedidos-compra/`](.kiro/specs/conector-pedidos-compra/) e guiaram toda a
  implementação depois.
- **Implementação** — todo o código Python (domínio, normalização, adapters, serviços, API,
  storage) foi escrito com a IA, tarefa por tarefa, seguindo o `tasks.md`.
- **Testes** — a suíte de testes automatizados (93 testes) foi escrita junto com cada
  funcionalidade, não depois.
- **Docker** — `Dockerfile`, `.dockerignore` e a validação de build/run.
- **Documentação** — README, exemplos de uso, e os próprios documentos de spec.

Não usei nenhuma outra ferramenta de IA (não usei Copilot, ChatGPT, Gemini etc.) — só o Claude
Code, numa sessão contínua.

## Um exemplo de uso que funcionou bem

**Contexto**: implementação da conversão de unidade de compra do cliente Gama (`CX` +
`fator_conv` → unidade de estoque), que é a parte mais delicada do desafio.

**O que pedi** (prompt real, depois de já termos as tasks T41/T42 definidas no `tasks.md`):
> "siga para T42" — task que dizia: *"Estender `app/integrations/gama/adapter.py` para aplicar a
> conversão descrita em `design.md` quando `um == 'CX'`: `quantity_ordered`, `quantity_received`
> e `unit_price` recalculados; `uom` canônico vira `'UN'`."*

**O que aconteceu e o que aproveitei**: a IA implementou a fórmula de conversão e, por conta
própria, testou contra os três itens de exemplo reais do enunciado — não só os que dividem exato
(`10 CX × fator_conv=12`), mas também um que gera dízima (`4 CX`, `fator_conv=3`,
`R$100,00 ÷ 3 = R$33,333...`). Ao testar esse segundo caso, ela percebeu que arredondar o preço
unitário *no momento da conversão* geraria um falso `PRICE_MISMATCH` depois, numa conferência de
nota fiscal correta (`12 × R$33,33 = R$399,96 ≠ R$400,00`). A decisão final — não arredondar na
conversão, deixar o `Decimal` carregar a precisão inteira e arredondar só uma vez, no momento da
comparação — não estava no meu pedido nem no `design.md` original. Aproveitei essa solução
diretamente, porque a evidência (o teste rodando ao vivo) comprovava que era necessária; hoje ela
está documentada em `design.md` §4.4 e coberta por teste específico
(`tests/integrations/test_gama_adapter.py::test_cx_with_non_exact_division_preserves_total_value`).

## Um exemplo em que a IA errou ou me levou por um caminho ruim

Aconteceu mais de uma vez, em contextos diferentes — de erro de cálculo em teste a uma sugestão
de design tecnicamente válida, mas não ideal pro problema de negócio:

1. **Cálculo de saldo pendente errado num teste** (T27): a IA escreveu um teste esperando que uma
   conferência contra o pedido do Gama desse `COMPLIANT` usando `quantity=118`, mas o saldo
   pendente real daquele item era `96` (`120 − 24`). O teste falhou imediatamente ao rodar, com
   uma mensagem clara de `AssertionError`. A IA recalculou, corrigiu o valor pra `96`, e o teste
   passou. Só soube que dava pra confiar no resultado final porque o teste *falhou primeiro* —
   não porque a IA "disse que estava certo".
2. **Teste com nome e lógica contraditórios** (T46): a IA escreveu um teste chamado
   `test_quantity_in_boxes_is_treated_as_exceeding_pending`, mas a própria asserção dizia
   `COMPLIANT` — o nome prometia uma coisa, o código provava outra. Percebi isso lendo o teste
   depois de rodado (não bastou "passar" — o cenário que o nome descrevia não correspondia ao que
   ele realmente verificava). Pedi pra remover, em vez de deixar um teste confuso no repositório
   só porque "passava".
3. **Parar a conferência na primeira divergência**: na primeira versão da lógica de
   `invoice_check_service`, a abordagem era interromper a validação assim que a primeira
   divergência fosse encontrada e devolver só ela. Percebi que isso obrigaria a V360 a corrigir
   um problema, repetir a conferência, e só então descobrir o próximo — lento pra quem opera.

O que me deu segurança nos três casos não foi confiar na primeira resposta da IA, mas ter pedido
pra rodar os testes e mostrar o resultado a cada etapa, ter lido o que os testes realmente
afirmavam (não só se o status era verde), e ter parado pra avaliar se a solução mais simples
resolvia o problema real, não só o problema técnico.

## Como garanti que entendo o código que estou entregando

- **Conduzi a implementação tarefa por tarefa**, nunca deixando a IA avançar sozinha por várias
  tasks de uma vez — a cada task concluída, pedi uma explicação do que foi feito e só autorizei a
  próxima depois de entender.
- **Testei manualmente fora dos testes automatizados**: subi o servidor via Docker, testei os
  endpoints pelo Swagger e via `curl` real, inclusive encontrando e corrigindo (com ajuda da IA)
  uma situação real de imagem Docker desatualizada depois de mudanças de código.
- **Pedi explicações conceituais antes de aceitar sugestões**, não só código — por exemplo, pedi
  pra entender exatamente o que mudaria no código pra implementar um conceito novo (tipo um
  endpoint de recebimento de mercadoria) antes de decidir se valia a pena, o que expôs uma
  decisão de arquitetura real (qual seria a fonte de verdade de `quantity_received`) que eu
  precisaria resolver, não só aceitar um código pronto.
- **Revisei e editei documentação manualmente**: a reestruturação do `README.md` (seções,
  cortes, correções de frase) teve edições diretas minhas por cima do que a IA gerou, não só
  aprovação passiva.
