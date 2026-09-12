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

## Fase 5 — preparação da campanha empírica

Estado: em andamento em 11/09/2026. O secret é injetado somente no job protegido e
permanece mascarado. O runner passou a usar fallback Docker sem rede, filesystem
raiz somente leitura, usuário não-root e limites de recursos. A compatibilidade de
tokenização tornou-se um gate e o modelo foi fixado no snapshot
`gpt-4o-mini-2024-07-18`.

Incrementos técnicos publicados neste ciclo:

- `480106c0a461b11911c325d2a02bbf25682b0e05`: fallback de container endurecido;
- `3fed6821ab1fbd8140019dbc8601874105393710`: correção da montagem gravável;
- `596dcc7d065cf06787533492d9b039301440976a`: gate de tokenizador;
- `0ab198318521d22cd24b902f615a89e8aa0f586a`: tolerância de cold start no probe;
- `9d36f390e0972f52210e88bfb39f6f6a647409d4`: matriz de 66 runs materializada;
- `7f5dee3e00952a898691e8fef287d93cd62214f5`: baseline B0 leakage-safe;
- `8da58f95b0d727f2e4e5a788c6b707966688f922`: kill switch e journal de LLM;
- `eb86b567b4add0404d924a6650dc770afb4f89cf`: smoke manual de uma chamada.

A CI de branch [34657963619](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34657963619),
a CI da PR [34657967293](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34657967293)
e o preflight protegido [34657963667](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34657963667)
passaram. Após os dois gates seguintes, a CI de branch
[34719631682](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34719631682),
a CI da PR [34719633915](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34719633915)
e o preflight [34719631681](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34719631681)
também passaram. Localmente, Ruff e 75 testes offline passaram; quatro testes live
foram desmarcados. O relatório remoto registrou `api_calls_performed: 0`.

O ledger agora reserva tokens/custo antes do transporte, persiste cada chamada,
interrompe na ausência de metadados e sincroniza totais com o manifesto. O cliente
não faz retentativas internas. O workflow manual limita o primeiro smoke a uma
chamada, 512 tokens, 16 tokens de saída e US$ 0,001. Telemetrias OpenTelemetry e
ONNX Runtime foram desativadas nos workflows.

Foi identificado um gate de plataforma: `workflow_dispatch` só fica disponível
quando o arquivo existe na branch padrão. O job foi adicionalmente limitado à ref
`feat/mestrado-fase-5`. Uma PR separada deve levar apenas esse dispatcher inerte à
`main`; mesclá-la habilita o botão, mas não dispara a chamada.

O plano continua com `protocol_frozen: false`. Nenhum dos 15 runs B0 principais,
dos seis pilotos ou dos 45 runs generativos principais foi coletado. Testes de
implementação não serão apresentados como resultado científico. O detalhamento e
os hashes estão em [FASE_5_STATUS.md](FASE_5_STATUS.md).

## Próxima ação

Revisar e mesclar a PR separada do dispatcher na branch padrão. Depois, apresentar
o gate final ao responsável. Não selecionar a branch da Fase 5 nem despachar o
workflow sem autorização explícita para uma chamada e teto de US$ 0,001. Em caso
de autorização, executar uma vez, auditar os três artefatos e interromper antes
dos pilotos para nova decisão.
