# Fase 1 — ambiente e execução determinística

Estado: concluída em 10 de setembro de 2026.

## Identificação e entrada

Responsável: Ricardo Fernandes, com execução assistida e revisão baseada em testes.

Commit de entrada: `c9ce7420add7e0c36c45c8e1299dbb157f8ae8f1`, derivado do baseline técnico `423875f03e0e6d63e921df852c57d4398e31236e`.

Problemas de entrada: o resolvedor não instalava as dependências, o arquivo `uv.lock` não continha o grafo resolvido, a CLI inferia modo pela presença de chave, os stubs divergiam das APIs reais e a CI ocultava falhas de teste com `|| true`.

Requisitos relacionados: RNF01 e RF02.

## Mudanças

| Incremento | Commit remoto | Resultado |
| --- | --- | --- |
| Ambiente | `b187d70b9993138bea3045c597b934ffaee1f977` | Python restrito a 3.11, conflito de Tenacity resolvido, dependência `crewai-tools` não utilizada removida, Poetry adotado como gerenciador único e `poetry.lock` completo criado |
| Execução | `39e71004e9ace20a569486095e84084e9abc6a58` | Modos `mock` e `live` explícitos, importações live tardias, mock marcado como sintético, artefatos por run, falha live sem artefato deixa de gerar sucesso sintético |
| CI | `228c770c177459f0f84735783f4275b32999a8b5` | Ordem do workflow corrigida; instalação, lock, lint e testes tornados gates obrigatórios |

O mock não constrói a Crew, não inicializa WandB e grava `network_used: false` em seu resultado. O modo live rejeita `OPENAI_API_KEY` ausente ou vazia antes de iniciar persistência ou agentes. Os testes externos receberam o marcador `live` e não integram o gate offline.

## Verificação

Ambiente local de verificação: CPython 3.11.16 e Poetry 2.2.1.

| Comando | Resultado observado |
| --- | --- |
| `poetry check --lock` | lock válido |
| `poetry install --no-interaction` | instalação concluída a partir do lock; 210 pacotes no primeiro ambiente limpo |
| `poetry run ruff check src tests` | `All checks passed!` |
| `poetry run pytest -q` | 4 passaram e 4 testes live foram desmarcados |

A execução remota final foi o GitHub Actions [run 34509660031](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34509660031), no commit `228c770c177459f0f84735783f4275b32999a8b5`. O runner usou Ubuntu 24.04 e CPython 3.11.16. Os gates checkout, setup do Python, instalação do Poetry, instalação das dependências, validação do lock, lint e testes terminaram com sucesso. O log registrou `4 passed, 4 deselected in 2.58s`.

O teste negativo `test_live_mode_rejects_empty_api_key` confirma que o modo live não prossegue sem credencial válida. `test_cli_init_dry_run` confirma a conclusão do mock, a criação de checkpoint e resultados, e a marcação explícita de resultado sintético sem rede.

## Falhas preservadas

| Execução | Falha | Decisão derivada |
| --- | --- | --- |
| Runs `34476947081` e `34476898442` | faixa Python do projeto excedia o limite de `crewai-tools` | restringir o runtime suportado e resolver o grafo completo |
| Resolução local inicial | `crewai 0.51.x` exigia Tenacity menor que 9 | fixar `tenacity >=8.2.3,<9` |
| Resolução local seguinte | `crewai-tools 0.4.x` dependia de LanceDB indisponível no grafo e não era necessário pelo código efetivo | remover a dependência e os FileTools não usados |
| Run `34508081212` | instalação passou e o lint legado falhou | corrigir violações e manter lint como gate |
| Run `34509443240` | cache Poetry foi solicitado antes da instalação do executável | retirar cache prematuro; run seguinte passou |

Essas tentativas não foram apagadas nem reclassificadas como sucesso.

## Limites e continuidade

Esta fase não valida chamadas reais a modelos, Semantic Scholar ou ArXiv. Os quatro testes live continuam fora do gate offline e exigem protocolo próprio, credenciais e controle de custo. O modo replay ainda não foi implementado. Há avisos de migração do formato `tool.poetry` para a tabela `project`, sem impacto no lock ou nos gates atuais.

Critérios de saída satisfeitos: instalação limpa; um gerenciador e lock coerentes; CI verde; lint e testes obrigatórios; mock sem chave e sem inicialização de integrações live; erro de teste não é mais suprimido.

Próxima ação: iniciar a Fase 2 pelos schemas canônicos de resultado e manifesto, antes de alterar novamente scoring, persistência ou busca.
