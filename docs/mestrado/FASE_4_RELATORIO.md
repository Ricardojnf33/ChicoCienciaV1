# Fase 4 — busca estruturada e avaliação dos agentes

Estado: concluída em 11 de setembro de 2026, com validação local e remota aprovadas.

## Identificação e entrada

Responsável: Ricardo Fernandes, com execução assistida e validação determinística.

Commit de entrada: `585dca5`, encerramento documental validado da Fase 3.

Problemas de entrada: os filhos da árvore podiam representar o mesmo plano; hipótese e plano não tinham identidade verificável; profundidade e ramificação não eram parte do checkpoint; a fronteira podia voltar a selecionar trabalho concluído; o score aceitava um sinal visual booleano sem evidência; e B1, A e A0 existiam apenas no protocolo escrito.

Requisitos relacionados: RF05 e RNF04, além das descobertas D05 e D06.

## Decisão implementada

Hipótese e plano experimental passaram a ser contratos Pydantic separados. A identidade da hipótese deriva de seu enunciado normalizado, e a identidade do plano deriva da hipótese, da decisão e dos parâmetros. Uma expansão rejeita chaves de decisão duplicadas e cria filhos com intervenções distintas. Profundidade, ramificação máxima, hipótese, plano e metadados são preservados no JSON e na projeção SQLite.

A seleção considera somente nós `PENDING` ou `FAILED` presentes na fronteira. Um nó no limite de profundidade torna-se terminal e não é ressuscitado após a conclusão. A propagação continua atualizando toda a cadeia ancestral, mas agora parte de resultado canônico e decisões de avaliação explícitas.

Reviewer e VLM produzem `review.json` e `vlm_review.json`, com identidade de nó e tentativa, decisão, critérios, racional, evidências e hash no manifesto. As decisões admitidas são `APPROVED`, `REJECTED`, `NEEDS_REVISION` e `NOT_EVALUATED`. Ausência de avaliador confiável gera `NOT_EVALUATED`; aprovação exige avaliação efetiva e todos os critérios em `PASS`. VLM não pode declarar avaliação quando o nó não possui figura.

As variantes compartilham o mesmo processo, contratos, runner, scorer e objetivo. Somente os fatores previstos mudam:

| Variante | Topologia | Correção automática | Ramificação efetiva |
| --- | --- | --- | --- |
| B1 | sequência fixa | sim, até duas correções | 1 |
| A | árvore | sim, até duas correções | ramificação solicitada |
| A0 | árvore | não | ramificação solicitada |

O comando `compare` materializa um manifesto de campanha, fixa o SHA-256 do objetivo e executa B1, A e A0 sem alteração manual entre condições.

## Incrementos

| Incremento | Commit | Resultado |
| --- | --- | --- |
| Busca estruturada | `b5ade243c5976e0985aaf5d6c55350d3e1c86262` | Hipóteses e planos identificáveis, decisões distintas, limites persistidos e fronteira sem ressurreição |
| Avaliação e variantes | `703f54290bfc34d3b8a2c6c3dc81a38454511f00` | Reviewer/VLM verificáveis, estado `NOT_EVALUATED`, políticas B1/A/A0 e correção diferenciada |
| Protocolo executável | `9718c585f38ee035604056d03cf9e56652cb123c` | Um comando executa as três condições com objetivo e limites compartilhados |

## Verificação

Ambiente local: CPython 3.11.16, Poetry 2.2.1, Ruff 0.6.9 e pytest 8.4.2.

| Verificação | Resultado observado |
| --- | --- |
| `poetry run ruff check src tests` | aprovado |
| `poetry run pytest -q` | 50 testes aprovados e 4 testes live desmarcados |
| Ajuda de `init` e `resume` | variantes B1, A e A0 expostas e retomada preserva a variante do manifesto |
| Identidade de hipótese/plano | estável; parâmetros não serializáveis e decisões duplicadas são rejeitados |
| Limites de busca | ramificação limitada; profundidade terminal; nenhum nó concluído volta à fronteira |
| Reviewer ausente | arquivos de avaliação criados com `NOT_EVALUATED`; score não recebe aprovação implícita |
| VLM sem figura | tentativa de avaliação substantiva rejeitada |
| Falha recuperável em B1 e A | primeira tentativa `FAILED`, segunda `SUCCEEDED` |
| Mesma falha em A0 | uma tentativa `FAILED`, sem correção automática |
| Campanha mock B1/A/A0 | as três condições terminaram `SUCCEEDED` sem mudança manual |

A validação independente ocorreu no GitHub Actions [run 34617850898](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34617850898). Instalação limpa, lock, Ruff e pytest terminaram com sucesso no commit documental remoto `594a95c72f9d5143ab6af79e8496cf7de8953ef0`.

O smoke completo usou `objective.example.yaml`, orçamento 8, ramificação 2 e profundidade 3. O objetivo teve SHA-256 `f2baaaa18b43e7002897e61774766fd96ec7962c8dbc9b82763f09689e34f11e`.

| Variante | Tentativas concluídas | Profundidades | Estágios executados | Fronteira final |
| --- | ---: | --- | --- | ---: |
| B1 | 4 | 0–3 | PRELIM, TUNING, RESEARCH_GRADE e ABLATIONS | 0 |
| A | 8 | 0–3 | PRELIM, TUNING, RESEARCH_GRADE e ABLATIONS | 7 |
| A0 | 8 | 0–3 | PRELIM, TUNING, RESEARCH_GRADE e ABLATIONS | 7 |

Todos os resultados do smoke são sintéticos, com métrica fixture 0,5, score composto 0,4075 e Reviewer/VLM `NOT_EVALUATED`. Esses números demonstram transições, persistência e comparabilidade operacional; não demonstram qualidade de ML, novidade, validade científica ou desempenho de LLM.

## Como reproduzir

```bash
poetry install
poetry run ruff check src tests
poetry run pytest -q
poetry run python -m src.cli compare objective.example.yaml \
  --mode mock --budget 8 --branching 2 --max-depth 3 --max-branching 3
```

Cada campanha cria `comparison.json` e, para cada variante, `manifest.json`, `tree.json`, `run.db` e artefatos separados por nó e tentativa.

## Limites e momento da execução com LLM

Nenhuma chamada de LLM, VLM, Semantic Scholar ou W&B foi realizada na Fase 4. O modo mock valida controle e contratos, não o comportamento dos agentes generativos.

A execução completa com LLM pertence à Fase 5 e somente começa depois de três gates: smoke positivo do sandbox em host compatível; orçamento monetário e teto de tokens aprovados e gravados; e configuração de modelo, prompts, corpus e protocolo identificada por commit. Primeiro serão feitos seis pilotos, dois por condição generativa, em Iris e Wine. Os pilotos não entram na comparação principal. Após analisar falhas e congelar o protocolo, serão coletados os 45 runs generativos principais de B1, A e A0; os 15 runs B0 não usam LLM.

A avaliação visual permanecerá `NOT_EVALUATED` até existir figura válida e um avaliador configurado. A avaliação humana independente continua obrigatória para as alegações acadêmicas e não é substituída por Reviewer ou VLM.

## Saída e continuidade

Os critérios da Fase 4 foram satisfeitos localmente e repetidos pela CI: o mock percorre transições válidas; as condições variam somente topologia e correção conforme o desenho; e a comparação executa sem edição manual durante a campanha.

Próxima ação: preparar a Fase 5 sem iniciar consumo pago — executar o preflight do sandbox em host compatível, materializar os objetivos Iris/Wine/Digits, registrar seeds e orçamento no manifesto da campanha e aprovar o gate antes dos seis pilotos com LLM.
