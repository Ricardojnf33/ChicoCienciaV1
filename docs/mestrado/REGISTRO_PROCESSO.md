# Registro do processo de conclusão

## 10 de setembro de 2026

Solicitação: sintetizar o desenvolvimento, definir a versão final acadêmica, preparar um plano por fases e documentar sua evolução em commits.

Baseline confirmado: `423875f03e0e6d63e921df852c57d4398e31236e`. O estado auditado é uma PoC experimental, versão 0.1.0. A investigação anterior examinou código, CI, PR e resultados, com reprodução pontual do script Iris.

## Incremento documental D1

Mudança: baseline e matriz de rastreabilidade. Resultado: achados conectados aos requisitos e testes planejados. Código de produção: nenhuma alteração. Validação: revisão de fontes e coerência entre estado observado e texto.

Commit: `e7edf706b52090718071f1b138ed324167f510ac`.

## Incremento documental D2

Mudança: desenho acadêmico, protocolo comparativo e três decisões arquiteturais propostas. Resultado: questões de pesquisa, limites e avaliação definidos. Nenhum dos experimentos propostos foi executado.

Commit: `58ebbaf04e7b4d3ef4e872a2e63ba39bed6f6aec`.

## Incremento documental D3

Mudança: síntese autoral, plano de fases, roteiro de defesa, guia de documentação e modelo de registro. Resultado: pacote documental para orientar a execução. Validação realizada: 12 documentos não vazios, links locais resolvidos, 60 runs principais, 51 runs generativos incluindo pilotos e teto de planejamento de 2,04 milhões de tokens. A renderização e revisão do Word integram a entrega derivada posterior.

O SHA deste incremento é o commit que introduz esta versão do registro e pode ser consultado no histórico do arquivo.

## Fase 1 — ambiente e execução determinística

Estado: concluída em 10/09/2026. Foram publicados três incrementos:

- `b187d70b9993138bea3045c597b934ffaee1f977`: ambiente Python 3.11 e lock Poetry reproduzível;
- `39e71004e9ace20a569486095e84084e9abc6a58`: modos mock/live explícitos, correções de runtime, lint e testes;
- `228c770c177459f0f84735783f4275b32999a8b5`: correção final do workflow.

Resultado local: `poetry check --lock` válido, Ruff aprovado, 4 testes aprovados e 4 testes live desmarcados. Resultado remoto: [GitHub Actions 34509660031](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34509660031), com todos os gates aprovados. As falhas intermediárias e os limites estão preservados no [relatório da Fase 1](FASE_1_RELATORIO.md).

## Fase 2 — contratos, estados e artefatos

Estado: concluída em 10/09/2026. Foram publicados três incrementos técnicos:

- `763f0e7512e6219799b6663444db3093170257d6`: contratos canônicos e adaptador legado;
- `c1c57e5a5bb17b0569e32e604937452b56fef614`: integração do manifesto e validação das tentativas;
- `d51dc7ce8bcb2da67aa92df196e71230dba9f5cc`: replay controlado e promoção somente após validação.

Resultado local: Ruff aprovado, 22 testes aprovados e 4 testes live desmarcados. A execução mock manual produziu manifesto, árvore, SQLite e artefatos por nó/tentativa. Os detalhes, valores históricos preservados e limites estão no [relatório da Fase 2](FASE_2_RELATORIO.md).

## Fase 3 — runner controlado e recuperação

Estado: concluída em 11/09/2026, com restrição operacional documentada. Foram publicados cinco incrementos técnicos:

- `22a2613100d4978bda6be4d39cb0883e721072dd`: execução controlada, evidência direta e reconciliação;
- `dd91c247cab154b3a9cf31f95ba2d9cd2854cd99`: checkpoint atômico e rate limiter realmente compartilhado;
- `3db700c30b74345c525ff6efe75f3f6f00c3c493`: falhas externas e de recursos injetadas;
- `b8e9365a621fc719ebcf6922bfe9698d788b44f9`: separação entre decisão e execução, reconstrução SQLite e orçamento de tentativas;
- `73d9a7a2349db84ce4ceed6a1e4f32665f3eae26`: filesystem mínimo no sandbox.

Resultado local: lock válido, Ruff aprovado, 32 testes aprovados e 4 testes live desmarcados. O smoke mock com orçamento 2 terminou com duas tentativas aprovadas. O host negou namespaces; o live foi recusado como projetado. A CI remota [34553951163](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34553951163) aprovou todos os gates e repetiu 32 aprovações e 4 desmarcações. Detalhes e limites estão no [relatório da Fase 3](FASE_3_RELATORIO.md) e no [runbook](RUNBOOK_RECUPERACAO.md).

## Fase 4 — busca estruturada e avaliação dos agentes

Estado: concluída em 11/09/2026. Foram publicados três incrementos técnicos:

- `b5ade243c5976e0985aaf5d6c55350d3e1c86262`: hipóteses e planos estruturados, expansão distinta e limites de busca;
- `703f54290bfc34d3b8a2c6c3dc81a38454511f00`: contratos de Reviewer/VLM, estados verificáveis e variantes B1/A/A0;
- `9718c585f38ee035604056d03cf9e56652cb123c`: execução comparativa automatizada das três condições.

Resultado: Ruff aprovado, 50 testes aprovados e 4 testes live desmarcados. O smoke comparativo percorreu PRELIM, TUNING, RESEARCH_GRADE e ABLATIONS nas três condições, sem LLM e sem avaliação visual presumida. A CI remota [34617850898](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34617850898) aprovou todos os gates. Detalhes, limites e o gate da Fase 5 estão no [relatório da Fase 4](FASE_4_RELATORIO.md).

## Próxima ação registrada em 11/09/2026 (histórica)

Preparar a Fase 5 sem iniciar chamadas pagas: validar o sandbox em host compatível, adicionar B0 e a matriz dataset/seed ao manifesto, registrar orçamento financeiro e congelar configurações antes dos seis pilotos. As Fases 5 e 6 permanecem planejadas.


## 27/09/2026 — E00: retomada pelo roadmap v1.1

O responsável determinou uma nova branch por vez, PR e preparação do Actions,
com disparo manual e pausa antes do próximo incremento. O estado remoto foi
revalidado: main 4ba9739, Fase 5 03eaf5a, PR #7 aberta e último piloto falho.
A próxima ação histórica acima foi parcialmente superada pelo trabalho na branch
Fase 5; o status atual está no [índice E00](evidencias/e00-20260927/index.md).

Foram preparados roadmap HTML/JSON, snapshot, pendências, relatório final
cumulativo e validador manual sem LLM. Nenhum workflow foi disparado pelo agente;
a CI de push/PR permanece automática conforme configuração existente.

Próximo passo: usuário integra a PR documental após revisão/CI e executa
Roadmap E00 - manual evidence gate em main. Conferir o run e preservar evidências
antes de iniciar E01. G0 acadêmico e G2 continuam pendentes.


## 27/09/2026 — E00: gate documental remoto concluído

O responsável disparou manualmente o workflow `Roadmap E00 - manual evidence gate`. O [run 36350845233](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/36350845233), tentativa 1, concluiu `success` em `main`, no SHA `41857710afd66616423e80ce025f8ec676de7665`. O job `validate-evidence` e todas as etapas reportadas pela API concluíram com sucesso.

O relatório registrou 11/11 checks de integridade documental aprovados: arquivos obrigatórios, unicidade de IDs, âncoras HTML, paridade HTML/JSON, dependências, DAG acíclico, critérios de aceite, monitoramento, ressalva da Fase 5 e SHAs de snapshot. Contagens: 13 épicos, 40 histórias, 120 tarefas e 360 subtarefas. A validação fez zero chamadas de API de LLM.

O artifact `roadmap-e00-36350845233-1` (ID 10942187121) foi baixado. O SHA-256 do ZIP local confere com o digest da API (`0cbd794118c2b0fe19af9cea4b312117c999c8c1f76df7f1f3a10034940a9aac`). Foram versionados `report.json`, `summary.md`, `checksums.json` e `run-metadata.json` em `evidencias/e00-20260927/remote/`, antes do vencimento previsto para 26/12/2026.

**Limite da conclusão:** trata-se somente de integridade documental em CI. Nenhum teste da aplicação, execução live, validação científica ou E2E foi feito; G2 permanece `NOT_VALIDATED`, G0 acadêmico depende de informação do responsável e a Fase 5 foi apenas observada, não reexecutada. A próxima ação é revisar/integrar o PR desta evidência; E01 não foi iniciado.
