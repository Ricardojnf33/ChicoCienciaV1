# Runbook de execução e recuperação

## Objetivo

Este roteiro recupera um run interrompido sem apagar artefatos nem repetir uma tentativa já concluída. Execute apenas um processo por `run_id`.

## Preflight

```bash
poetry check --lock
poetry run ruff check src tests
poetry run pytest -q
```

Para modo live, confirme que `bwrap` e `prlimit` existem. O runner executa um preflight real do namespace antes do código gerado; presença do binário isoladamente não é suficiente. Falha de namespace é condição de parada, não autorização para desativar a política.

## Diagnóstico de um run

```bash
poetry run python -m src.cli inspect <run_id>
poetry run python -m src.cli report <run_id>
```

Preserve `runs/<run_id>/manifest.json`, `tree.json`, `run.db` e `artifacts/`. Não edite `status`, hash ou número de tentativa à mão. O manifesto é o registro de tentativas; SQLite é uma projeção reconstruível.

## Retomada

```bash
poetry run python -m src.cli resume <run_id> --budget 1
```

Comece com orçamento 1. Durante a carga, cada tentativa `SUCCEEDED` do manifesto tem resultado, identidade, modo, artefatos e SHA-256 revalidados. Se a árvore ainda não refletir o sucesso, ele será finalizado uma vez. Se já refletir, não haverá nova propagação nem novos filhos para a mesma tentativa.

## Estados esperados

| Situação | Comportamento esperado | Ação |
| --- | --- | --- |
| Manifesto `RUNNING`, tentativa `SUCCEEDED` | reconciliar árvore e continuar no próximo nó | retomar com orçamento 1 |
| Tentativa `FAILED`, orçamento restante | criar `attempt-<n+1>` sem sobrescrever a anterior | revisar erro e retomar |
| Tentativas esgotadas | nó e manifesto `FAILED`, checkpoint salvo | corrigir causa; não aumentar limite sem decisão registrada |
| Hash ou artefato divergente | abortar reconciliação | preservar arquivos e abrir investigação |
| Sandbox indisponível | abortar antes de executar código | mover o piloto para host compatível |
| Timeout | retorno 124, logs e evidência preservados | revisar script e orçamento antes de nova tentativa |

## Verificação posterior

Confirme que os pares `(node_id, attempt)` no manifesto são únicos, que cada sucesso aponta para `results.json` válido e que o número de visitas do nó não cresce ao repetir uma retomada sem orçamento. Rode novamente a suíte offline após qualquer correção.

O modo de teste `require_network_isolation=False` não deve ser usado para pilotos, coleta ou demonstração live.
