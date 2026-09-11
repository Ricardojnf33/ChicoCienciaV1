# Fase 5 — status da preparação empírica

Estado: em andamento em 11 de setembro de 2026. O preflight protegido está verde,
a matriz da campanha foi materializada e o baseline B0 foi implementado e testado.
O protocolo permanece em rascunho (`protocol_frozen: false`), a coleta principal
não começou e nenhuma chamada à API da OpenAI foi realizada.

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

## Evidência reproduzível

No commit remoto `7f5dee3e00952a898691e8fef287d93cd62214f5`, os três
workflows terminaram com sucesso:

| Verificação | Execução | Resultado |
| --- | --- | --- |
| CI da branch | [34657963619](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34657963619) | PASS |
| CI da pull request | [34657967293](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34657967293) | PASS |
| Preflight protegido | [34657963667](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34657963667) | PASS |

O artefato `phase5-preflight`, ID `10285864187` e digest
`sha256:47c22c06c95d3bf0cdc15b6245d3a78c0d97950f48b4bd453bdf559345897a73`,
registra todos os gates como PASS e `api_calls_performed: 0`. O runtime observado
foi Python 3.11.16, CrewAI 0.51.1 e setuptools 80.10.2. O runner usou o backend
Docker e a imagem `sha256:2474eadc82cc0ea9460a1348432bf1df584a42a173c2bdd2f69af6601343154c`.

Localmente, Ruff passou e `pytest -q` registrou 65 testes aprovados e quatro testes
live desmarcados. Os novos testes exercitam os três datasets e confirmam uma única
avaliação do teste reservado, custo/tokens LLM iguais a zero e rejeição de uma
especificação generativa pelo executor B0. Nenhum dos 15 resultados B0 principais
foi coletado: os testes são validação do mecanismo, não amostra científica.

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

1. Aplicar os limites de tokens e custo como kill switch no caminho live, com
   contabilidade por chamada e por run testada sem rede.
2. Criar um workflow de smoke de uma única chamada, manual, protegido pelo
   environment `phase5-pilot`, sem executá-lo durante a implementação.
3. Congelar prompts, versões, protocolo e plano por commit após revisão explícita.
4. Apresentar o preflight final e o custo máximo ao responsável e obter autorização
   explícita para a primeira chamada real.
5. Se o smoke passar, executar os seis pilotos; analisar artefatos, custo, redaction
   e desvios antes de decidir pelo congelamento e pela coleta principal.

O próximo incremento técnico é o gate 1. A presença do secret e o preflight verde
não autorizam consumo. A primeira chamada real continua proibida até autorização
explícita do responsável.
