# E01 Contrato de geração antes da execução

## Baseline e incidente

A [PR #12](https://github.com/Ricardojnf33/ChicoCienciaV1/pull/12) integrou o
registro documental do E00 à main em `fe1e370`. O E01 parte de `03eaf5a`, head
da [PR #7](https://github.com/Ricardojnf33/ChicoCienciaV1/pull/7), onde existe o
caminho live que materializa o retorno da Crew. A PR do E01 tem a branch da
Fase 5 como base.

O [run 35047877307](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35047877307)
foi o dispatch de número 5. O preflight passou. O piloto B1/Iris falhou, cinco
jobs foram cancelados e o agregador falhou. Os
[logs do piloto](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35047877307/job/104641937673)
mostram consultas bibliográficas repetidas. Antes da mensagem de parada, o
ledger recusou uma chamada cuja projeção acumulada era de 43.548 tokens, acima
do teto de 40.000. O executor posteriormente recebeu a mensagem de parada como
`code.py` e registrou `SyntaxError` na linha 1.

O [bundle histórico](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35047877307/artifacts/10427188662)
teve o SHA-256 conferido antes da leitura. Nas três tentativas, `code.py`
continha a mesma mensagem de parada. O manifesto e o journal coincidem em
18 chamadas contabilizadas, 37.620 tokens, US$ 0,00719325 e 157 reservas
recusadas. Os totais incluem o uso anterior preservado pelo workflow.

| Arquivo histórico | SHA-256 |
| --- | --- |
| ZIP | `1eeb694f26660f3588e9cb1094894886874e87c0cd58fb35a77c4f757de1611a` |
| `code.py` das três tentativas | `030ddf0a9d2ec3328151bd6671aeafc844737ffecc6cd6b0e7ad0dd5f603041e` |
| `manifest.json` | `dc51756cd38b4140f01ef7659e16ef8962e74464bcf8e4f724e3e9b69217e10b` |
| `llm-budget.json` | `4cfa50e7bf99902e33be92231c4db70b4d22bcfc38e43172a9e48edc9e76d2bb` |

São dois pontos de intervenção. O E01 impede a materialização de uma resposta
inválida. O padrão de chamadas bibliográficas repetidas e o comportamento da
Crew após a recusa do ledger orientam o próximo incremento, com o teto atual
como restrição. O log documenta a sequência observada em um piloto. Ele não
isola uma causa para todas as falhas futuras de geração.

## E01.H01 a E01.H03

- H01. A fixture do teste replica apenas a mensagem de parada, sem contexto,
  prompts, credenciais ou conteúdo bibliográfico do run. Antes da correção, o
  teste desse caso chegou à sentinela que representa o acionamento do runner.
- H02. O contrato exige um bloco Python cercado e sem prosa externa. O
  orquestrador compila os bytes UTF-8 sem executar e só então grava
  `code.py` atomicamente. O runner isolado e a validação do resultado mantêm
  suas funções. O campo de erro existente distingue `GENERATION_INVALID` e
  `GENERATION_LIMIT_REACHED`, com motivo sanitizado e sem a resposta do modelo.
- H03. Os testes exercitam falhas e retomada pelas políticas de B1, A e A0.
  B1 e A permitem três tentativas por nó. A0 permite uma. Após esgotar esse
  limite, o manifesto conserva as tentativas anteriores e a retomada recusa
  trabalho adicional. Se o ledger bloquear novas chamadas, a falha encerra a
  execução sem usar as tentativas restantes. A retomada do mesmo journal
  preserva uso e custo e recusa um novo kickoff com `LLM_BUDGET_STOPPED`.
  Um teste com o ledger real verifica essa transição, com Crew e runner simulados.

## Validação local e no Actions

A suíte local em Python 3.11 passou com 110 testes aprovados e quatro testes live excluídos da execução. Ruff e `poetry check --lock` passaram.

O workflow **CI** testa o lock, Ruff e a suíte offline em Python 3.11. O
artefato `offline-tests-<run_id>-<run_attempt>` contém o JUnit da execução.
A execução de PR é automática. Para registrar a validação manual do
responsável, usar **Re-run all jobs** no run de CI vinculado à PR do E01.
Conferir o commit, a tentativa e o JUnit antes de registrar G1 e avançar.
O workflow dos seis pilotos é separado e tem seu próprio gate de autorização.

O E01 usa zero chamadas de modelo. A evidência é de contrato, recuperação e
teste offline. A validação ponta a ponta de um piloto real pertence a G2.
