# Fase 5 — status do preflight empírico

Estado: em andamento em 11 de setembro de 2026. A credencial e o runtime foram
validados no ambiente protegido, mas o gate do runner permanece fechado. Nenhuma
chamada à API da OpenAI foi realizada.

## Escopo deste marco

Este marco prepara a avaliação empírica sem iniciar coleta paga. Foram eliminados
stubs silenciosos do caminho live, a chave passou a ser `SecretStr`, e sua entrega
aos clientes de LLM e aos agentes CrewAI tornou-se explícita. O adaptador de
ferramentas agora usa o contrato real do LangChain. O runtime foi estabilizado em
Python 3.11, CrewAI 0.51.1 e setuptools 80.10.2, pois essa versão do CrewAI ainda
depende de `pkg_resources`.

O comando `preflight` valida credencial, runtime, objetivo, modelos e runner, grava
um relatório JSON e não instancia uma requisição OpenAI. O workflow usa o GitHub
Environment `phase5-pilot` e recebe `OPENAI_API_KEY` somente pelo contexto do job.

## Evidência observada

No commit remoto `25b5bb67051640cdc7edcea40da4c5fb5f3d8216`, a CI geral
[34630881170](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34630881170)
terminou com sucesso. O preflight protegido
[34630881158](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34630881158)
produziu o seguinte resultado:

| Gate | Resultado | Evidência |
| --- | --- | --- |
| Credencial | PASS | `OPENAI_API_KEY` presente e mascarada |
| Runtime | PASS | Python 3.11.16, CrewAI 0.51.1, setuptools 80.10.2 |
| Objetivo | PASS | `objective.example.yaml` legível |
| Modelos | PASS | nomes textual e visual preenchidos |
| Runner | FAIL | namespace direto negado; montagem da virtualenv negada no fallback |
| Chamadas OpenAI | 0 | `api_calls_performed: 0` no artefato do workflow |

A sequência negativa foi preservada nos runs
[34629503293](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34629503293),
[34630317413](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34630317413) e
[34630617444](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34630617444).
Ela localizou três restrições distintas: configuração de loopback sem privilégio,
exigência de user namespace para redução de UID e acesso à virtualenv após a troca
de namespace. Em todas as tentativas, os demais gates passaram e o contador de API
permaneceu zero.

Localmente, Ruff foi aprovado e `pytest -q` registrou 58 testes aprovados e quatro
testes live desmarcados. Os testes cobrem mascaramento do secret, rejeição de chave
ausente, injeção explícita nos agentes reais, ausência de chamada no preflight e
falha fechada do sandbox.

## Decisão de segurança

O projeto não desativará o isolamento apenas para obter um workflow verde. Código
gerado continua sem credenciais, sem rede e sujeito a limites de CPU, memória,
arquivo e tempo. Como o `bubblewrap` não obteve prova positiva no GitHub-hosted
runner, o piloto live está bloqueado.

A próxima implementação deve substituir o fallback experimental por um backend
de container com imagem identificada por digest, filesystem somente leitura,
diretório de tentativa gravável, `--network none`, usuário não-root e limites de
recursos. O mesmo backend deve executar um probe positivo e um teste negativo de
rede antes de qualquer piloto.

## Gates ainda pendentes

1. Implementar e validar o sandbox de container sem enfraquecer RNF03.
2. Verificar a compatibilidade de tokenização dos modelos escolhidos com a versão
   congelada de CrewAI/tiktoken; um nome de modelo preenchido não prova isso.
3. Materializar B0, objetivos Iris/Wine/Digits, seeds e hashes no manifesto.
4. Registrar teto de tokens, custo máximo, limite de tentativas e kill switch.
5. Congelar protocolo e prompts por commit.
6. Apresentar o preflight final ao responsável e obter autorização explícita.

Somente depois desses seis gates será permitido um smoke de uma chamada pequena.
Se ele passar e custo, artefatos e redaction forem confirmados, serão executados os
seis pilotos previstos. Pilotos não compõem a amostra principal. A coleta de 60
runs permanece posterior ao congelamento do protocolo e a uma decisão explícita de
continuidade.

## Critério de continuidade

Este documento não encerra a Fase 5. Ele encerra o marco de captura do secret e
registra um bloqueio reproduzível do runner. O próximo commit técnico deve tratar
o backend de isolamento; B0 e a matriz experimental podem ser preparados offline,
mas nenhuma alegação empírica com LLM pode ser produzida antes do preflight verde.
