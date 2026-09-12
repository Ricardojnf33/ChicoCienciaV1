# Fase 5 — status da preparação empírica

Estado: em andamento, atualizado em 12 de setembro de 2026. O preflight protegido
está verde, a matriz da campanha foi materializada, o baseline B0 foi implementado
e o kill switch de tokens/custo está ativo no caminho live. Um workflow manual de
uma chamada foi preparado, mas não executado. O protocolo permanece em rascunho
(`protocol_frozen: false`), a coleta não começou e nenhuma chamada à API da OpenAI
foi realizada.

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
US$ 0,03 no run. A resposta substitui a reserva pelo uso informado pelo provedor;
ausência de metadados cobra a reserva integral e bloqueia novas chamadas. O journal
por chamada e os totais no manifesto permitem retomada auditável. Retentativas
internas do cliente foram desativadas (`max_retries=0`); recuperações pertencem ao
orquestrador e, portanto, permanecem visíveis.

O workflow `Phase 5 one-call smoke` aceita somente despacho manual, usa o
environment `phase5-pilot`, exige a frase `I_AUTHORIZE_ONE_OPENAI_CALL` e reduz os
limites para 512 tokens, 16 tokens de saída e US$ 0,001. Ele executará primeiro o
preflight zero-call e só então uma invocação. A resposta não é armazenada; apenas
seu hash, aderência ao sentinel, tokens, custo e contagens serão preservados.

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
desativadas, Ruff passou e `pytest -q` registrou 75 testes aprovados e quatro testes
live desmarcados. Além da B0, os testes cobrem reserva e rejeição pré-transporte,
contabilização por chamada, timeout, metadados ausentes, retomada do journal,
sincronização com manifesto, autorização do smoke e recusa de mais de uma chamada.
Nenhum resultado principal foi coletado: são testes do mecanismo, não amostra
científica.

## Identidade e limites da campanha

| Item | Valor |
| --- | --- |
| Plano | `phase5-draft-v1` |
| SHA-256 do plano | `d907aac11365c06f1f8f8245e5909bdb79c5aca1d2803a6cf53d997b63ebf906` |
| Datasets | Iris, Wine e Digits |
| Seeds | 11, 23, 37, 51 e 71 |
| Condições principais | B0, B1, A e A0; 15 runs cada |
| Pilotos | 2 B1, 2 A e 2 A0; somente Iris/Wine |
| Modelo | `gpt-4o-mini-2024-07-18` |
| Limite por run generativo | 6 tentativas, 2 correções por nó, 900 s, 40.000 tokens e US$ 0,03 |
| Limite da campanha | 2.040.000 tokens e US$ 1,53 |

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

## Gates pendentes

1. Apresentar este preflight, o teto de US$ 0,001 e a semântica de uma única chamada
   ao responsável; obter autorização explícita antes de despachar o workflow.
2. Se autorizado, executar o smoke uma vez e inspecionar resposta, redaction,
   tokens, custo, journal e ausência de retentativa automática.
3. Somente após smoke aprovado e nova autorização, executar os seis pilotos.
4. Analisar os pilotos, registrar eventuais ajustes e congelar prompts, versões,
   protocolo e plano por commit.
5. Executar B0 e a matriz principal apenas depois do congelamento.

O próximo passo é um gate humano, não uma ação automática. A presença do secret,
o preflight verde e a existência do workflow não autorizam consumo. A primeira
chamada real continua proibida até autorização explícita do responsável.
