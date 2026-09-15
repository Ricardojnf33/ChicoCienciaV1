# Fase 5 — status da preparação empírica

Estado: em andamento, atualizado em 14 de setembro de 2026. O preflight protegido
está verde, a matriz da campanha foi materializada, o baseline B0 foi implementado
e o kill switch de tokens/custo está ativo no caminho live. O smoke autorizado foi
executado uma única vez e aprovado. O protocolo permanece em rascunho
(`protocol_frozen: false`), os pilotos não começaram e nenhum resultado principal
foi coletado.

## Resultado deste incremento

O runner científico dispõe agora de fallback Docker com filesystem raiz somente
leitura, rede desativada, capacidades removidas, `no-new-privileges`, usuário
não-root, limites de processos, CPU, memória e tempo, além de apenas um diretório
de tentativa gravável. O probe importa o stack científico, confirma que
`OPENAI_API_KEY` não chega ao código gerado e exige que uma conexão de rede falhe.
A evidência registra o backend e o identificador da imagem usada.

A versão congelada de CrewAI traz `tiktoken` 0.7, que não reconhece a família
`gpt-4.1-mini`. Por isso, o preflight passou a rejeitar modelos sem tokenizador
compatível e a campanha fixou `gpt-4o-mini-2024-07-18` para texto e visão. Essa é
uma decisão de compatibilidade reproduzível, não uma alegação de qualidade.

O plano `phase5-draft-v1` contém 66 especificações: seis pilotos generativos e 60
runs principais, formados por quatro condições, três datasets e cinco seeds. A
ordem principal é reprodutível pela seed 20260911. São 51 runs generativos no
total; B0 possui tokens e custo de LLM iguais a zero.

O pipeline B0 carrega Iris, Wine e Digits localmente, reserva 20% por split
estratificado, seleciona `C` entre 0,1, 1 e 10 por validação cruzada estratificada
de cinco folds apenas sobre os 80% de treino e avalia o teste uma única vez.
Hashes do dataset e dos índices de treino/teste, scores de validação, parâmetro
selecionado, métricas, duração e contadores de LLM são gravados no resultado.

Cada chamada live reserva, antes do transporte, os tokens estimados de entrada e a
saída máxima. A chamada é recusada se a projeção ultrapassar 40.000 tokens ou
US$ 0,03 no run. Um terceiro kill switch limita explicitamente cada run generativo
a 24 chamadas iniciadas, incluindo falhas de transporte. A resposta substitui a
reserva pelo uso informado pelo provedor;
ausência de metadados cobra a reserva integral e bloqueia novas chamadas. O journal
por chamada e os totais no manifesto permitem retomada auditável. Retentativas
internas do cliente foram desativadas (`max_retries=0`); recuperações pertencem ao
orquestrador e, portanto, permanecem visíveis.

O workflow `Phase 5 one-call smoke` aceita somente despacho manual, usa o
environment `phase5-pilot`, exige a frase `I_AUTHORIZE_ONE_OPENAI_CALL` e reduz os
limites para 512 tokens, 16 tokens de saída e US$ 0,001. Ele executará primeiro o
preflight zero-call e só então uma invocação. A resposta não é armazenada; apenas
seu hash, aderência ao sentinel, tokens, custo e contagens serão preservados.
O job também exige `refs/heads/feat/mestrado-fase-5`, de modo que um despacho na
branch padrão seja recusado antes de carregar o secret.

## Resultado do smoke real

O run manual
[34890553182](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34890553182)
foi executado em 14/09/2026 sobre o commit
`9f5e278ff6dea8b26336dd560b8c9906d3008673` e terminou em PASS. O artefato
`phase5-one-call-smoke`, ID `10366926127`, digest
`sha256:196e4e8f400ef59d293e1cab29eebdf95569b370bcdbaca9151b36b84e2e73c6`,
contém três arquivos JSON e registrou:

| Medida | Resultado |
| --- | --- |
| Modelo | `gpt-4o-mini-2024-07-18` |
| Chamadas iniciadas/concluídas/falhas | 1 / 1 / 0 |
| Tokens de entrada/saída/total | 18 / 5 / 23 |
| Custo observado | US$ 0,0000057 |
| Duração da chamada | 4,578 s |
| Sentinel | hash preservado e `response_matches_expected: true` |
| Retentativas internas | 0 |

A resposta textual não foi persistida. O artefato preserva somente o SHA-256
`be18e5fa97f1c7176d72e71dfb12627fae2e04610eeb14c6cff419bc8e2760e5`, a
confirmação do sentinel, uso, custo e contadores. O preflight imediatamente anterior
registrou `api_calls_performed: 0`, credencial mascarada e todos os gates em PASS.
Portanto, a evidência sustenta apenas a conectividade e a contabilização do caminho
live; ela não constitui resultado científico do sistema multiagente.

## Evidência reproduzível

No commit remoto `eb86b567b4add0404d924a6650dc770afb4f89cf`, os três
workflows terminaram com sucesso:

| Verificação | Execução | Resultado |
| --- | --- | --- |
| CI da branch | [34719631682](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34719631682) | PASS |
| CI da pull request | [34719633915](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34719633915) | PASS |
| Preflight protegido | [34719631681](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34719631681) | PASS |

O artefato `phase5-preflight`, ID `10305807446` e digest
`sha256:65350e03ae1a6fa15496e9bcd77849d86cd3ae138d1725981f1dec6b9b361b7f`,
registra credential, runtime, objective, models, budget e runner como PASS, além de
`api_calls_performed: 0`. O runtime observado foi Python 3.11.16, CrewAI 0.51.1 e
setuptools 80.10.2. O runner usou backend Docker e a imagem
`sha256:fdf396b11a76a89680a64179d35b3fefc6b6e7241742ec57decaa99a95bbf41a`.

Localmente, com telemetrias OpenTelemetry e ONNX Runtime explicitamente
desativadas, Ruff passou e `pytest -q` registrou 90 testes aprovados e quatro testes
live desmarcados. Além da B0, os testes cobrem reserva e rejeição pré-transporte,
contabilização por chamada, timeout, metadados ausentes, retomada do journal,
sincronização com manifesto, autorização do smoke, recusa de mais de uma chamada,
propagação de seed e retomada dos seis pilotos sem reexecução. Nenhum resultado
principal foi coletado: são testes do mecanismo, não amostra científica.

## Ensaio offline do executor de pilotos

O comando `run-pilots` materializa exclusivamente as seis especificações
`kind=pilot`, cria um manifesto agregado e um manifesto por run e pode retomar um
checkpoint sem repetir runs já concluídos. Uma retomada é recusada se o hash do
plano, o modo, o objetivo ou um checkpoint parcial divergirem. O caminho `live`
falha antes de construir a Crew sem a autorização literal separada
`I_AUTHORIZE_SIX_PILOT_RUNS`.

A seed da especificação passou a integrar o manifesto de cada run, o estado do
orquestrador e o parâmetro `seed` do modelo. O prompt do Coder também exige seu uso
em `random`, NumPy, partições e estimadores aplicáveis. Isso registra a intenção de
reprodutibilidade sem alegar determinismo integral de uma API externa.

Um ensaio CLI em diretório temporário executou B1, A e A0 nas seis identidades do
plano e terminou com seis estados `SUCCEEDED`, seeds 11/11/23/23/37/37 e consumo
agregado igual a zero chamadas, zero tokens e US$ 0. Os scores sintéticos do mock
não são dados piloto e não serão usados na dissertação.

## Workflow dos seis pilotos preparado

O workflow `Phase 5 six-pilot campaign` aceita apenas `workflow_dispatch` e exige
branch, primeira execução, primeira tentativa e a autorização literal
`I_AUTHORIZE_SIX_PILOT_RUNS`. Um preflight zero-call antecede a matriz fechada. Os
seis jobs usam `max-parallel: 1`, ledger próprio, runner isolado e timeout duro de
15 minutos no passo experimental. A saída bruta da Crew foi desativada nos logs.

Cada job publica um bundle independente mesmo em falha e verifica se a credencial
foi persistida. O job final roda com `always()`, baixa os seis bundles e recusa
artefatos ausentes, identidades ou modos divergentes, limites inconsistentes,
journal diferente do manifesto, reserva ativa e totais acima dos tetos. Em sucesso,
produz `pilot-campaign-report.json` e `pilot-checksums.json`.

O ensaio local reproduziu a topologia da matriz com seis processos mock separados,
seguido pelo agregador: seis runs aprovados, 19 hashes SHA-256 e consumo LLM zero.
O workflow foi publicado na branch da Fase 5, mas ainda não foi despachado nem está
disponível na `main`.

O primeiro commit remoto dessa preparação,
`84e77fe5bf2e13e249e3e086372b7911b4d3d81c`, passou no preflight protegido
[34909994055](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34909994055).
As CIs detectaram uma dependência indevida do teste de `--help` em relação à
renderização Rich do terminal. O contrato da CLI foi mantido e o teste passou a
inspecionar diretamente os parâmetros Typer/Click. A correção remota
`6e0d3d7a814fd0166f8e532bdb9e483903bb5298` passou na CI de push
[34956663122](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34956663122),
na CI da PR
[34956665985](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34956665985)
e no preflight protegido
[34956663106](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34956663106).
Nenhum desses checks executou os pilotos ou chamou a OpenAI.

## Identidade e limites da campanha

| Item | Valor |
| --- | --- |
| Plano | `phase5-draft-v1` |
| SHA-256 do plano | `eaac40d89cb3206ec27138bd43580a1b5ab6c9c824ff4bc70595d2a4d8badea4` |
| Datasets | Iris, Wine e Digits |
| Seeds | 11, 23, 37, 51 e 71 |
| Condições principais | B0, B1, A e A0; 15 runs cada |
| Pilotos | 2 B1, 2 A e 2 A0; somente Iris/Wine |
| Modelo | `gpt-4o-mini-2024-07-18` |
| Limite por run generativo | 6 iterações, 2 correções por nó, 900 s, 24 chamadas, 40.000 tokens e US$ 0,03 |
| Limite dos seis pilotos | 144 chamadas, 240.000 tokens, US$ 0,18 e 5.400 s se sequenciais |
| Limite da campanha | 1.224 chamadas, 2.040.000 tokens e US$ 1,53 |

Os preços registrados no plano são US$ 0,15 por milhão de tokens de entrada,
US$ 0,075 para entrada em cache e US$ 0,60 por milhão de tokens de saída, conforme
a [página oficial do modelo](https://developers.openai.com/api/docs/models/gpt-4o-mini),
consultada em 11/09/2026. O teto de US$ 0,03 por run é deliberadamente mais
conservador que uma estimativa baseada apenas em 40 mil tokens, pois o mix real de
entrada/saída ainda não foi observado. O teto de US$ 1,53 é a soma fail-closed dos
51 limites individuais, não consumo realizado.

Hashes dos objetivos:

- Digits: `3dee40822f1a79084816e17e56da5a0e31997741ade468c6d74163a8b221d5ad`;
- Iris: `0078b221ba0b8fa54e200f71926063e1d8717cac29495edda4aa889a469464e3`;
- Wine: `2ffba70c1a67c1cd4edad6d610cbe44bf4e467dc9580f2657e8e74f108539b60`.

## Histórico do gate de segurança

As falhas anteriores do `bubblewrap` continuam preservadas nos runs
[34629503293](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34629503293),
[34630317413](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34630317413) e
[34630617444](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34630617444).
Elas localizaram restrições de namespace e montagem do GitHub-hosted runner. O
fallback de container resolveu o bloqueio sem remover isolamento; o primeiro
preflight verde foi o run
[34640925508](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34640925508).

## Gates seguintes

1. Integrar em PR separada somente o dispatcher inerte à `main`, condição necessária
   para que o GitHub apresente o botão manual.
2. Revalidar o teto global de 144 chamadas, 240.000 tokens e US$ 0,18 antes do
   despacho.
3. Obter autorização separada antes de executar os seis pilotos.
4. Analisar os pilotos, registrar eventuais ajustes e congelar prompts, versões,
   protocolo e plano por commit.
5. Executar B0 e a matriz principal apenas depois do congelamento.

## Ativação do dispatcher do smoke concluída

Em 13/09/2026, as PRs #2 a #6 foram integradas à `main` mediante revalidação por
fase. A PR #8 foi então atualizada sobre a nova baseline, passou na CI de push
[34770519991](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34770519991)
e na CI do PR
[34770521733](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34770521733),
e foi mesclada no commit `f569b66fa8aa0436f05686b4619beb065fa67be4`.
Essa integração apenas tornou o controle manual visível na branch padrão; não
despachou o workflow. A presença do secret, o preflight verde e a existência do
workflow não autorizam consumo. A primeira chamada real continua proibida até
autorização explícita do responsável.

Em 14/09/2026, após a auditoria do único run, o workflow foi desabilitado
manualmente no GitHub Actions. O repositório continua registrando exatamente um
evento `workflow_dispatch`, run `34890553182`, tentativa 1, concluído com sucesso.
