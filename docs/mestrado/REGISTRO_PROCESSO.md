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
`feat/mestrado-fase-5`. A PR #8 foi aberta separadamente e contém somente esse
dispatcher inerte. Seu CI
[34720268555](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34720268555)
falhou em `Install deps`, antes de lint e testes, porque a `main` ainda referencia
`crewai-tools (^0.4.0)`. O dispatcher não foi executado e nenhuma chamada ocorreu.
Para preservar o escopo auditável da PR #8, a correção de dependências não foi
misturada nela.

Em 13/09/2026, a integração foi executada por gates. A PR #3 foi retargeteada para
`main` e incorporou a PR #2 junto da correção de runtime; depois, as PRs #4, #5 e
#6 foram retargeteadas, revalidadas individualmente e mescladas. A PR #8 foi
atualizada sobre essa baseline e passou nas CIs
[34770519991](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34770519991)
e [34770521733](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34770521733).
O dispatcher foi integrado à `main` em
`f569b66fa8aa0436f05686b4619beb065fa67be4`. Nenhum desses eventos despachou o
smoke ou acessou a API da OpenAI.

Em 14/09/2026, após autorização literal, o run manual
[34890553182](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34890553182)
executou o smoke exatamente uma vez e terminou em PASS. O journal registrou uma
chamada iniciada, uma concluída, zero falhas, 18 tokens de entrada, cinco de saída,
23 no total e custo de US$ 0,0000057. O sentinel correspondeu ao esperado; somente
seu hash foi persistido. O artefato `phase5-one-call-smoke` tem ID `10366926127` e
digest `sha256:196e4e8f400ef59d293e1cab29eebdf95569b370bcdbaca9151b36b84e2e73c6`.
Nenhum piloto ou run principal foi iniciado.

Após a confirmação visual de `Workflow disabled successfully`, o dispatcher do
smoke passou ao estado operacional desabilitado. A consulta de runs continuou
mostrando exatamente um `workflow_dispatch`, sem reexecução. Na preparação dos
pilotos foi identificado que tokens e custo limitavam indiretamente chamadas
concluídas, mas falhas de transporte não consumiam esses tetos. Foi então adicionado
um kill switch explícito de 24 chamadas iniciadas por run. O plano passa a limitar
os seis pilotos a 144 chamadas, 240.000 tokens, US$ 0,18 e 5.400 segundos se
executados sequencialmente. Nenhum piloto foi executado durante essa alteração.

Na sequência, o executor `run-pilots` foi construído e ensaiado integralmente em
modo mock. Ele selecionou somente as seis specs piloto, persistiu seed e identidade
por run, agregou chamadas/tokens/custo e retomou estados concluídos sem reexecução.
O caminho live exige a autorização literal separada
`I_AUTHORIZE_SIX_PILOT_RUNS` antes da construção da Crew. A seed passou a ser
encaminhada também ao parâmetro do modelo e à instrução do código experimental.
O ensaio terminou com seis runs mock aprovados e consumo LLM zero; seus valores
sintéticos não constituem dados científicos.

O executor foi então separado em `run-pilot`, adequado a um job de matriz, e
`aggregate-pilots`, que reconcilia os seis bundles sem receber a credencial. O
workflow manual preparado exige primeira execução/tentativa, branch da Fase 5 e a
autorização literal antes do environment. O preflight antecede os jobs; a matriz
usa `max-parallel: 1` e timeout de 15 minutos por execução; o agregador roda mesmo
após falha para tornar artefatos ausentes observáveis. Um ensaio com seis processos
mock independentes terminou em PASS, gerou 19 checksums e registrou zero chamadas,
tokens e custo. O workflow não foi despachado.

A preparação foi publicada na branch da Fase 5 no commit remoto
`84e77fe5bf2e13e249e3e086372b7911b4d3d81c`. O preflight protegido
[34909994055](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34909994055)
passou sem acessar a API. As CIs de branch
[34909993965](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34909993965)
e da PR
[34909997947](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34909997947)
encontraram uma única falha após 89 aprovações e quatro desmarcações: o teste da
opção `--mode` dependia da saída Rich de `--help`, que varia conforme largura e
capacidades do terminal. O contrato real da CLI e o workflow não falharam. O teste
foi corrigido para inspecionar diretamente os parâmetros Typer/Click, sem depender
da apresentação do terminal. Após a correção, o gate local voltou a registrar 90
testes aprovados, quatro testes live desmarcados, Ruff aprovado e lock válido.
Nenhum workflow de piloto foi despachado e nenhuma chamada OpenAI ocorreu nessa
correção.

A correção foi publicada no commit remoto
`6e0d3d7a814fd0166f8e532bdb9e483903bb5298`. A CI de push
[34956663122](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34956663122),
a CI da PR
[34956665985](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34956665985)
e o preflight protegido
[34956663106](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34956663106)
terminaram em PASS. Assim, a publicação e a validação remota do executor e do
workflow dos seis pilotos foram concluídas sem dispatch e com consumo LLM zero.

Em seguida, a PR separada
[#9](https://github.com/Ricardojnf33/ChicoCienciaV1/pull/9) foi criada a partir da
`main` com somente `.github/workflows/phase5-pilots.yml`. As CIs de push
[34957322305](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34957322305)
e da PR
[34957357810](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34957357810)
passaram. Após confirmação do diff unitário, ela foi mesclada em
`1f92ce2180c6e7ae27de9eed76a2c2d5e995b117`; a CI pós-merge
[34957492480](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34957492480)
também passou. O dispatcher tornou-se visível na branch padrão, mas permaneceu com
zero execuções. A integração não constituiu autorização e não consumiu a API.

O gate pré-autorização recalculou o arquivo da campanha e confirmou seis pilotos,
144 chamadas, 240.000 tokens, US$ 0,18 e 5.400 segundos sequenciais. O hash do
arquivo permaneceu idêntico ao valor fixado no workflow. Durante a verificação, o
workspace reciclou o interpretador do `.venv`; o ambiente local foi preservado e
reconstruído em Python 3.11.16 a partir do lockfile. Depois de carregar no cache
transitório apenas a tabela pública `o200k_base` do tokenizador, 90 testes passaram,
quatro live foram desmarcados, Ruff passou e o lock permaneceu válido. As falhas
intermediárias foram de integridade do ambiente e cache do tokenizador, anteriores
à execução da Crew. Não houve dispatch ou chamada OpenAI.

Após a autorização literal, o primeiro dispatch dos seis pilotos, run
[34980482902](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34980482902),
falhou em 12 segundos no primeiro gate de identidade. O SHA-256 do plano presente
na branch remota divergia do valor congelado; a inspeção do blob confirmou bytes
inválidos introduzidos na publicação anterior pela API Git. Nenhuma dependência foi
instalada, a Crew não foi construída, os jobs `pilots` e `aggregate` foram
desmarcados e nenhuma chamada OpenAI ocorreu. A anotação de artefato ausente foi
secundária: o preflight não havia chegado a produzir o arquivo. O run número 1
permanece consumido e não deve ser reexecutado. A correção reserva somente o run
número 2, primeira tentativa, e exige republicação Base64 do plano com conferência
do blob Git antes de nova autorização.

A recuperação foi publicada com correspondência exata entre todos os blobs locais
e remotos; o plano passou a apontar para
`e1f2138831a7eb3c2ab144a98f586d3e65c7ece5`. A CI de push
[34982320599](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34982320599),
a CI da PR #7
[34982327631](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34982327631)
e o preflight protegido
[34982320606](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34982320606)
passaram. A PR unitária
[#10](https://github.com/Ricardojnf33/ChicoCienciaV1/pull/10) atualizou o dispatcher
da `main`, passou nas CIs de push
[34982733031](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34982733031)
e de PR
[34982804866](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34982804866),
foi mesclada em `4ba97396dcc02aa53d2da4a3365c463df313ce5d` e passou na CI pós-merge
[34982993230](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34982993230).
O histórico ainda contém somente o run número 1; o run número 2 não foi iniciado.

O plano continua com `protocol_frozen: false`. Nenhum dos 15 runs B0 principais,
dos seis pilotos ou dos 45 runs generativos principais foi coletado. Testes de
implementação não serão apresentados como resultado científico. O detalhamento e
os hashes estão em [FASE_5_STATUS.md](FASE_5_STATUS.md).

## Incidente do segundo dispatch e correção do manager

Em 16/09/2026, o run
[35043495688](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35043495688)
passou no preflight e iniciou apenas `pilot-01-b1-iris-s11`. O contrato do
manager hierárquico falhou porque `build_manager` fornecia explicitamente
`tools=[]`, proibido por CrewAI 0.51.1 para esse papel. O `fail-fast` cancelou
os outros cinco pilotos e a agregação recusou corretamente a ausência dos bundles.

A evidência preservada contabilizou uma chamada concluída, 2.829 tokens e
US$ 0,00134595, sem falha de transporte e sem persistência da credencial. O
incidente não produziu resultado científico. A correção e a proteção contra
regressão foram publicadas nos commits
`aeaba14775b086a16f87d54a58e70e49e63e031a` e
`b9eaf14a77890b8d1f221739a4ab68300d370ad1`.

A topologia de recuperação foi publicada em
`fa79d5358ce571aa83dd149432e8fee23732f287` e validada pelo teste do commit
`ba5a4706525ca2f945ae4d2ed0375a4c7f62fbcc`. Ela restaura o bundle do piloto
01 a partir do artefato `10426096904`, preserva consumo e tentativas anteriores,
retoma esse checkpoint e executa separadamente apenas os cinco pilotos inéditos.
A CI [35044299063](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35044299063)
e o preflight
[35044299050](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35044299050)
passaram sem novas chamadas.

## Run 3 e revisão estrutural do caminho live

O run
[35044828531](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35044828531)
passou no preflight. O piloto 01 preservou a chamada anterior e foi interrompido
sem novo consumo por já possuir três tentativas. O piloto 02 iniciou uma chamada,
registrou 2.829 tokens e US$ 0,00134595 e reproduziu a falha do manager; os demais
foram cancelados. O acumulado dos pilotos é duas chamadas, 5.658 tokens e
US$ 0,00269190, sem piloto concluído.

A investigação confirmou três lacunas do contrato live: mutação das ferramentas
de delegação do manager entre kickoffs, descarte do código retornado pela Crew e
ausência de usage metadata no formato esperado. Elas foram corrigidas nos commits
`d7cefafba93c093890de66027f796dcc3e1a1aa3`,
`843c0f138a03f52c8abba839fcfd2efc0f07108b`,
`908195ec036f6428aa8c4e66b1e3d81bc0ec679f` e
`3d5e903452a86e4d10b40e08d6144e83caf54102`, com regressões cobertas por
`230346dc45400f5d52031e228bdc232f8535f91e` e
`5b37a2b7abc27d28418a2200c3a899e667ecbe3c`. A CI
[35045553230](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35045553230)
e o preflight
[35045553274](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35045553274)
passaram sem novas chamadas.

## Próxima ação

Não usar `Re-run jobs` nos runs 2 ou 3. O dispatcher continua fechado no run 3
já consumido. Antes de publicar um run 4, revisar e autorizar explicitamente a
recuperação que importará somente os journals dos pilotos 01 e 02 para preservar
as duas chamadas anteriores, reiniciando manifests e árvores inválidos sem ampliar
o teto total de 144 chamadas.

## Recuperação run 4 publicada e autorizada

A autorização `I_AUTHORIZE_PHASE5_RECOVERY_RUN4` foi registrada. O dispatcher
`f9b99d96eca8cf60cc4841a8e23e1d7a26d79f01` implementa uma recuperação
journal-only: importa somente os ledgers dos pilotos 01 e 02 do run 3 e cria novos
manifestos, árvores, banco e estados de execução. Os demais quatro pilotos começam
limpos. As seis identidades continuam sequenciais e fechadas por fail-fast.

Os testes de contrato foram atualizados em
`6b94b3b1e150dcb65d90edd12e6ae5a557798f12` e corrigidos em
`588000277f56fbaafe690a615dc69d6e379a4259`. A CI
[35046474015](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35046474015)
e o preflight
[35046473848](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35046473848)
passaram. A preparação não chamou a OpenAI.

O teto agregado não foi reiniciado: as duas chamadas e 5.658 tokens anteriores
continuam contabilizados. O run 4 permanece não iniciado e deverá ser disparado
uma única vez, manualmente, na branch da Fase 5. Reexecuções dos runs 2 e 3
continuam proibidas.

## Gate consumido do run 4

A auditoria final do histórico identificou que o run
[35046059553](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35046059553)
já havia consumido `run_number == 4` no commit
`34b5cc3798059a56320e46c2aaea1af340663279`. O dispatcher então vigente
aceitava somente o run 3; por isso o evento foi integralmente `skipped` em dois
segundos. Não houve job de piloto nem chamada OpenAI.

Como números de run não são reutilizáveis, a autorização do run 4 não foi
reinterpretada como autorização do run 5. A publicação de um novo gate foi
interrompida, mantendo o sistema inerte. O trabalho somente continuará após a
autorização literal `I_AUTHORIZE_PHASE5_RECOVERY_RUN5`.

## Run 5 autorizado e preparado

A autorização `I_AUTHORIZE_PHASE5_RECOVERY_RUN5` permitiu rearmar o gate sem
reinterpretar a autorização anterior. O dispatcher foi atualizado em
`6a5fca44efcf11b87d186e305c7f60a19b5f3ec3` e seu teste de contrato em
`cb89e70d6fde4d9f487c7dcfe68b65f6a3a4acf8`.

A CI [35047113023](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35047113023)
e o preflight
[35047113037](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35047113037)
passaram sem executar pilotos ou acessar a API. O run 5 está apto a um único
despacho manual, mantendo as duas chamadas anteriores no teto agregado.

