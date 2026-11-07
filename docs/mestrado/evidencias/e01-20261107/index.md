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
  suas funções. `GENERATION_INVALID` é registrado no campo de erro existente,
  com motivo sanitizado e sem a resposta do modelo.
- H03. Os testes exercitam falhas e retomada pelas políticas de B1, A e A0.
  B1 e A permitem três tentativas por nó. A0 permite uma. Após esgotar esse
  limite, o manifesto conserva as tentativas anteriores e a retomada recusa
  trabalho adicional. O ledger real tem testes offline próprios no mesmo
  workflow. A Crew e o runner são substituídos por fixtures no teste do E01.

## Validação local e no Actions

A suíte local em Python 3.11 passou com 109 testes aprovados e quatro testes live excluídos da execução. Ruff e `poetry check --lock` passaram.

O workflow **CI** testa o lock, Ruff e a suíte offline em Python 3.11. O
artefato `offline-tests-<run_id>-<run_attempt>` contém o JUnit da execução.
A execução de PR é automática. Para registrar a validação manual do
responsável, usar **Re-run all jobs** no run de CI vinculado à PR do E01.
Conferir o commit, a tentativa e o JUnit antes de registrar G1 e avançar.
O workflow dos seis pilotos é separado e tem seu próprio gate de autorização.

O E01 usa zero chamadas de modelo. A evidência é de contrato, recuperação e
teste offline. A validação ponta a ponta de um piloto real pertence a G2.
