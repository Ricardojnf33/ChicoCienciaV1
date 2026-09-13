# Fase 2 — contratos, estados e artefatos

Estado: concluída em 10 de setembro de 2026.

## Identificação e entrada

Responsável: Ricardo Fernandes, com execução assistida e validação por testes.

Commit de entrada: `0ee04f48e50b4c79cf15fb3e219df6446f2ae034`, encerramento validado da Fase 1.

Problemas de entrada: JSON de resultado livre, scorer silenciosamente convertido para zero, formatos históricos aninhados incompatíveis, sucesso parcial por existência de arquivo, ausência de manifesto canônico e tentativas sem diretório e identidade próprios.

Requisitos relacionados: RF02, RF03, RF04 e parte de RF06.

## Decisão implementada

O contrato `1.0` define resultado canônico e manifesto com Pydantic. Um resultado `SUCCEEDED` exige:

- identidade de nó e tentativa;
- modo `mock`, `live` ou `replay`;
- métrica primária presente, finita e entre zero e um;
- `return_code = 0`;
- coerência entre modo e marcação sintética;
- arquivos declarados existentes, com tamanho e SHA-256 correspondentes.

Resultados históricos não são modificados. O comando `replay` recebe o caminho explícito da métrica e uma redução declarada, produzindo um novo resultado canônico. O sistema rejeita inferência automática quando o JSON legado é aninhado.

## Incrementos

| Incremento | Commit remoto | Resultado |
| --- | --- | --- |
| Contratos | `763f0e7512e6219799b6663444db3093170257d6` | Schemas de resultado, evidência, artefato, tentativa e manifesto; adaptador legado; validação de identidade, hashes e duplicatas |
| Runtime | `c1c57e5a5bb17b0569e32e604937452b56fef614` | Scorer canônico, manifesto integrado, estados por tentativa e layout por run/nó/tentativa |
| Replay e promoção | `d51dc7ce8bcb2da67aa92df196e71230dba9f5cc` | CLI de replay, preservação de fonte histórica e promoção do nó somente depois da validação |

## Estrutura observada

Cada diretório `runs/<run_id>/` contém `manifest.json`, `tree.json`, `run.db` e os resultados em `artifacts/<node_id>/attempt-<n>/results.json`.

No modo live, a tentativa também exige `code.py`, `raw_results.json` e `execution.json`. O arquivo canônico referencia esses artefatos e seus hashes.

## Verificação

Ambiente local: CPython 3.11.16 e Poetry 2.2.1.

| Verificação | Resultado observado |
| --- | --- |
| `poetry run ruff check src tests` | aprovado |
| `poetry run pytest -q` | 22 testes aprovados e 4 testes live desmarcados |
| CLI mock com orçamento 2 | manifesto `SUCCEEDED`, duas tentativas aprovadas, dois resultados canônicos, árvore e SQLite criados |
| Código existente com retorno 1 | rejeitado; não se torna resultado canônico |
| Código sem resultado | rejeitado; nenhum fallback sintético é criado em live |
| Resultado inválido na árvore | nó mantém `results_path=None`, `score=None` e permanece na fronteira |
| Tentativa duplicada | manifesto rejeitado |
| Artefato alterado depois do registro | divergência de hash rejeitada |

Os testes de replay preservaram os valores versionados:

| Fonte histórica | Caminho declarado | Valor preservado |
| --- | --- | --- |
| Iris `c7d345b0` | `l2.10.mean_accuracy` | 0,9800000000000001 |
| Wine | `average_f1_scores.logreg_l2` | 0,9730857138960456 |
| Iris `d5068c16` | `hypothesis_2.accuracies`, redução máxima | 0,9777777777777777 |

A evidência remota final é o GitHub Actions [run 34543573124](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34543573124).

## Descoberta durante a fase

Um teste de regressão revelou que `AgenticTree.update_result()` gravava o caminho do resultado antes de calcular o score. Quando a validação falhava, o nó permanecia parcialmente alterado. A operação foi invertida: o score é calculado primeiro e a promoção só ocorre depois do sucesso.

## Limites

Nenhuma chamada live foi executada. No fluxo live atual, `execution.json` ainda é materializado pelo workflow dos agentes; a captura direta e independente do retorno do subprocesso, o bloqueio de rede e a remoção verificável de credenciais pertencem à Fase 3. As gravações ainda não são atômicas e a retomada idempotente não foi atestada.

O manifesto registra estados e hashes, mas o SQLite continua como projeção do runtime existente. Reconstrução da projeção, migração e tolerância a interrupção permanecem pendentes.

## Saída e continuidade

Critérios satisfeitos: artefato inválido não promove nó; scorer consome apenas contrato válido; métricas históricas são adaptadas sem alterar a origem; duplicatas são rejeitadas; tentativa e execução possuem identidade e diretório próprios.

Próxima ação: Fase 3, começando pelo runner que captura diretamente retorno, stdout e stderr em evidência verificável, seguido por timeout, ambiente sem credenciais, checkpoint atômico e retomada idempotente.
