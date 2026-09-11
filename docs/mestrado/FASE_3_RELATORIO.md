# Fase 3 — runner controlado e recuperação

Estado: concluída em 11 de setembro de 2026, com verificação operacional do isolamento pendente em host Linux que permita namespaces de usuário.

## Identificação e entrada

Responsável: Ricardo Fernandes, com execução assistida e validação determinística.

Commit de entrada: `115af255a560a528229e0c798cb2f9318063e555`, encerramento validado da Fase 2.

Problemas de entrada: o agente Runner declarava o próprio retorno, subprocessos herdavam o ambiente completo, timeout não preservava evidência, checkpoint e manifesto não eram atômicos, uma interrupção entre manifesto e árvore podia repetir trabalho e o rate limiter compartilhava lock, mas não o timestamp efetivo.

Requisitos relacionados: RF04, RF06, RNF02 e RNF03.

## Decisão implementada

O processo decisório e a execução foram separados. Researcher e Coder produzem plano e `code.py`; o orquestrador chama um componente determinístico que produz `execution.json`, `stdout.log` e `stderr.log`. O Coder não possui mais a ferramenta de execução e o antigo agente Runner não integra a equipe ativa.

O runner live aplica:

- ambiente por allowlist, sem chaves, tokens, senhas, `HOME` ou configuração do usuário;
- namespace Bubblewrap com rede separada e capabilities removidas;
- filesystem mínimo: runtime e bibliotecas somente para leitura, `/tmp` efêmero e apenas o diretório da tentativa gravável;
- limites de CPU, memória virtual, tamanho de arquivo, core dump e descritores via `prlimit`;
- timeout de parede e encerramento do grupo de processos com `SIGTERM` e `SIGKILL`;
- recusa da execução quando o host não fornece isolamento de rede do sistema operacional.

O parâmetro `require_network_isolation=False` existe somente para testes unitários locais das demais políticas. O fluxo live do orquestrador não o utiliza.

Manifesto, resultado e árvore usam gravação temporária, `fsync` e troca atômica no mesmo diretório. Na retomada, tentativas `SUCCEEDED` são validadas por identidade e SHA-256 e aplicadas uma única vez. Marcadores impedem nova propagação de score e nova expansão. A projeção SQLite é repovoada a partir da árvore carregada. O número da próxima tentativa deriva do manifesto; o sistema não sobrescreve tentativa anterior e encerra o nó após o orçamento permitido.

## Incrementos

| Incremento | Commit | Resultado |
| --- | --- | --- |
| Runner e recuperação | `22a2613100d4978bda6be4d39cb0883e721072dd` | Evidência direta, limites, timeout, gravação atômica e reconciliação de sucesso durável |
| Persistência e rate limiter | `dd91c247cab154b3a9cf31f95ba2d9cd2854cd99` | Checkpoint atômico, relógio monotônico e estado global entre instâncias |
| Falhas determinísticas | `3db700c30b74345c525ff6efe75f3f6f00c3c493` | Fixtures de timeout externo e orçamento de recursos sem serviço real |
| Separação de responsabilidades | `b8e9365a621fc719ebcf6922bfe9698d788b44f9` | Coder sem execução, Runner fora da equipe decisória, reconstrução SQLite e orçamento de tentativas |
| Fronteira do sandbox | `73d9a7a2349db84ce4ceed6a1e4f32665f3eae26` | Raiz do host removida da visão do processo; montagem restrita ao runtime e à tentativa |

## Verificação

Ambiente local: CPython 3.11.16, Poetry 2.2.1 e Ruff 0.6.9.

| Verificação | Resultado observado |
| --- | --- |
| `poetry check --lock` | aprovado; apenas avisos de metadados Poetry depreciados |
| `poetry run ruff check src tests` | aprovado |
| `poetry run pytest -q` | 32 testes aprovados e 4 testes live desmarcados |
| Smoke mock com orçamento 2 | manifesto `SUCCEEDED` com duas tentativas e árvore, SQLite e artefatos criados |
| Credencial injetada no processo pai | ausente no script filho |
| Timeout com processo filho | retorno 124; grupo encerrado; sentinela do filho não foi criada |
| Arquivo acima do orçamento | execução falhou; arquivo não ultrapassou o limite configurado |
| Falha durante `os.replace` | checkpoint anterior preservado e temporário removido |
| Manifesto concluído e árvore interrompida | resultado aplicado uma vez; uma visita e um conjunto de filhos após duas retomadas |
| Orçamento de tentativa esgotado | nó, manifesto e checkpoint terminaram em `FAILED`; tentativa anterior preservada |
| Duas instâncias Semantic Scholar | intervalo compartilhado de 1,25 s comprovado com relógio falso, sem espera real |
| Timeout Semantic Scholar | exatamente três chamadas pela fixture e exceção final preservada |
| Sandbox indisponível | execução recusada antes do código gerado |

A validação remota ocorreu no GitHub Actions [run 34553951163](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34553951163). Checkout, Python 3.11, Poetry 2.2.1, instalação limpa, lock, Ruff e testes passaram. O log remoto registrou 32 testes aprovados e 4 desmarcados em 4,70 s.

O host desta sessão possui `bubblewrap`, mas nega a criação do namespace. Esse resultado não foi convertido em bypass: o teste de fail-closed confirma a recusa. A prova positiva de uma chamada live dentro do namespace deve ser executada em host compatível e sem consumo de LLM antes da coleta da Fase 5.

## Descobertas durante a fase

O lock global do Semantic Scholar não bastava: `self._last_request_time` criava timestamps por instância. A correção acessa o estado pela classe, usa relógio monotônico e permite relógio e sleeper injetados.

A proposta inicial montava a raiz do host como somente leitura. Embora impedisse escrita, permitiria leitura desnecessária de arquivos. A implementação final cria uma visão mínima do filesystem. A revisão também identificou que manter a ferramenta no Coder permitiria execução antes do controle orquestrado; essa capacidade foi removida.

## Limites

Nenhuma chamada live, LLM, Semantic Scholar ou W&B foi realizada. Os testes sem namespace exercitam subprocesso, limites e timeout, mas não são evidência de isolamento contra código hostil. Bubblewrap reduz a superfície de risco e o fluxo falha fechado, porém não constitui garantia absoluta contra falhas do kernel ou do próprio mecanismo de sandbox.

Os arquivos JSON são atomicamente substituídos, mas manifesto e árvore não formam uma transação única entre arquivos. A reconciliação idempotente trata a janela de interrupção conhecida. Concorrência de dois processos sobre o mesmo run permanece fora do escopo e deve ser impedida operacionalmente.

## Saída e continuidade

Os critérios de saída de código foram satisfeitos: falha injetada preserva o checkpoint anterior; tentativa concluída não é reaplicada; timeout e orçamento encerram o trabalho; credenciais não atravessam o boundary; falha de isolamento impede live; tentativas anteriores continuam no manifesto.

Próxima ação: Fase 4, estruturando hipóteses e decisões distintas, limites de profundidade e ramificação, estados explícitos de Reviewer/VLM e as variantes comparativas B1, A e A0. O [runbook de recuperação](RUNBOOK_RECUPERACAO.md) deve acompanhar qualquer piloto.
