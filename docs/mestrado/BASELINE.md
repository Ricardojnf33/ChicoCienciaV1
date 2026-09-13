# Baseline auditado do Chico Ciência

Data de corte: 10/09/2026. Revisão: `423875f03e0e6d63e921df852c57d4398e31236e`.

Status: diagnóstico documentado. Este registro preserva os achados da investigação anterior; não indica que as correções foram implementadas.

## 3 Descobertas do desenvolvimento

### 3 1 Evolução observada

| Período | Evidência no repositório | Aprendizado |
| --- | --- | --- |
| Outubro de 2025 | CLI, scoring, árvore e persistência | A estrutura do fluxo pode ser exercitada com dados sintéticos |
| Novembro de 2025 | Registro 70f8222b e artefatos de execução | Sucesso do processo precisa ser distinguido de execução científica real |
| Novembro de 2025 | Correções do runner e experimento d5068c16 | Caminhos de arquivos e ferramentas disponíveis condicionam a autonomia |
| Janeiro de 2026 | Experimentos Iris e Wine e textos acadêmicos | Métricas plausíveis exigem revisão do desenho experimental e do contrato de dados |
| Janeiro de 2026 | PR 1 com Streamlit | A visualização depende da consistência do estado e dos artefatos |
| Agosto de 2026 | README explicitando o caráter experimental | O posicionamento do projeto passou a reconhecer limites de validação |

Essa cronologia descreve o histórico versionado. Não permite inferir atividades locais que não foram publicadas. [E1, E6–E8]

### 3 2 Descobertas que alteram a arquitetura

| ID | Descoberta | Mudança de projeto proposta |
| --- | --- | --- |
| D01 | A CI falha antes dos testes e o comando pytest ignora o código de erro | Instalação reproduzível e falha real como bloqueio de integração |
| D02 | O scorer espera métrica na raiz, mas os artefatos têm estruturas aninhadas | Modelo canônico de resultados e adaptação explícita de formatos históricos |
| D03 | A existência de code.py pode ser aceita como sucesso | Sucesso condicionado ao término da execução e à validação dos artefatos |
| D04 | O fallback sintético pode ocorrer no fluxo real | Modos separados, sem promoção de fixtures para evidência real |
| D05 | A consistência visual recebe valor verdadeiro por padrão | Avaliação com estados aprovado, reprovado e não avaliado |
| D06 | Filhos podem herdar o mesmo plano sem hipóteses distintas | Hipóteses estruturadas, identidade própria e eliminação de duplicatas |
| D07 | Arquivos e checkpoint não formam um registro suficiente de execução | Manifesto, hashes, eventos e restauração idempotente |
| D08 | O rate limiter não compartilha efetivamente o timestamp entre instâncias | Estado compartilhado verificado por teste de relógio controlado |

A auditoria também identificou um `json.dump` sem o nome `json` importado, stubs incompatíveis com argumentos usados no runtime e execução de Python por subprocesso sem isolamento reforçado. Esses achados são requisitos de correção, não provas de vulnerabilidade explorada. [E2, E3, E9]

### 3 3 Mudança de entendimento

Minha hipótese inicial de desenvolvimento privilegiava a coordenação entre agentes. A investigação mostrou que a fronteira crítica está na validação das transições. Passar de código escrito para experimento concluído exige verificar retorno do processo, integridade do JSON, métrica esperada e vínculo com o nó. Passar de resultado numérico para conclusão exige conferir o desenho experimental e a incerteza.

Por isso, proponho concentrar o mestrado na engenharia dessas transições. A interface e o texto final serão consumidores de evidência validada. A autonomia será descrita pelo que foi executado sem intervenção e pelo que permaneceu sob decisão humana.

## 4 Resultados disponíveis e seus limites

| Evidência | Resultado | Limite de interpretação |
| --- | --- | --- |
| Iris d5068c16 | Baseline 88,89%; melhor L2 95,56%; melhor combinação 97,78% | Experimento histórico isolado |
| Iris c7d345b0 | Baseline 96,67%; L2 com C 10 ou 100 chega a 98,00% | Ganho observado de 1,33 ponto percentual; p aproximadamente 0,1778 |
| Wine | F1 macro 95,5852% no baseline e 97,3086% com L2 | Ganho de 1,7234 ponto percentual; p igual a 0,3125 |
| Reprodução local do Iris na auditoria | Principais médias e p-valor recuperados; saída 0 | Reprodução do script, sem recriar a geração pelos agentes |
| CI de 15/08/2026 | Instalação falhou; lint e testes ignorados | Não fornece resultado da suíte |

Os valores vêm dos artefatos versionados e da verificação pontual registrada na auditoria. O ambiente daquela reprodução utilizou scikit-learn 1.8.0, NumPy 2.3.5 e SciPy 1.17.0. Não será apresentado como o ambiente oficial da avaliação final. [E4–E6]

No Iris, o baseline já utiliza a regularização padrão da regressão logística. A comparação representa ajuste de intensidade. O mesmo conjunto de folds orienta a escolha de C, o que recomenda separar seleção e avaliação na próxima rodada. No Wine, a implementação chamada dropout mascara entradas durante a predição após treinar sem dropout. A queda para 36,99% de F1 descreve essa implementação, e não fundamenta uma conclusão geral sobre dropout.

Os testes históricos de L2 não alcançam significância no nível de 5%. Isso não demonstra ausência de efeito; limita a força da conclusão com a evidência disponível. A matriz de confusão do Wine é calculada sobre dados usados no treinamento final e será substituída por predições fora da amostra. A alegação histórica de ganho de produtividade de cerca de 23 vezes será retirada da conclusão científica até existir uma comparação controlada. [E4–E6, E10]

## 17 Fontes e evidências

As referências E identificam o baseline e os artefatos do projeto. As referências R fundamentam o enquadramento e decisões metodológicas. Consulta realizada em 10/09/2026.

E1. Ricardo Fernandes. ChicoCienciaV1. [Revisão auditada e README](https://github.com/Ricardojnf33/ChicoCienciaV1/tree/423875f03e0e6d63e921df852c57d4398e31236e).

E2. [Orquestração ATS no baseline](https://github.com/Ricardojnf33/ChicoCienciaV1/blob/423875f03e0e6d63e921df852c57d4398e31236e/src/processes/ats_process.py).

E3. [Scoring](https://github.com/Ricardojnf33/ChicoCienciaV1/blob/423875f03e0e6d63e921df852c57d4398e31236e/src/core/scoring.py) e [árvore](https://github.com/Ricardojnf33/ChicoCienciaV1/blob/423875f03e0e6d63e921df852c57d4398e31236e/src/core/tree.py).

E4. Iris c7d345b0. [Código](https://github.com/Ricardojnf33/ChicoCienciaV1/blob/423875f03e0e6d63e921df852c57d4398e31236e/experiments/c7d345b0/code.py) e [resultados](https://github.com/Ricardojnf33/ChicoCienciaV1/blob/423875f03e0e6d63e921df852c57d4398e31236e/experiments/c7d345b0/experiments/c7d345b0/results.json).

E5. GitHub Actions. [Execução de 15/08/2026](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/31860336365) e [workflow do baseline](https://github.com/Ricardojnf33/ChicoCienciaV1/blob/423875f03e0e6d63e921df852c57d4398e31236e/.github/workflows/ci.yml).

E6. Wine. [Código cbd7a4c9](https://github.com/Ricardojnf33/ChicoCienciaV1/blob/423875f03e0e6d63e921df852c57d4398e31236e/experiments/cbd7a4c9/code.py) e [resultados](https://github.com/Ricardojnf33/ChicoCienciaV1/blob/423875f03e0e6d63e921df852c57d4398e31236e/experiments/results.json).

E7. [Registro do teste 70f8222b](https://github.com/Ricardojnf33/ChicoCienciaV1/blob/423875f03e0e6d63e921df852c57d4398e31236e/reports/live_test_70f8222b_20251108_175928.json) e [resultado d5068c16](https://github.com/Ricardojnf33/ChicoCienciaV1/blob/423875f03e0e6d63e921df852c57d4398e31236e/experiments/d5068c16/results.json).

E8. [PR 1 de visualização Streamlit](https://github.com/Ricardojnf33/ChicoCienciaV1/pull/1).

E9. [Cliente Semantic Scholar](https://github.com/Ricardojnf33/ChicoCienciaV1/blob/423875f03e0e6d63e921df852c57d4398e31236e/src/clients/semantic_scholar_client.py), [runner](https://github.com/Ricardojnf33/ChicoCienciaV1/blob/423875f03e0e6d63e921df852c57d4398e31236e/src/tools/python_repl.py) e [construção da equipe](https://github.com/Ricardojnf33/ChicoCienciaV1/blob/423875f03e0e6d63e921df852c57d4398e31236e/src/crews/ai_scientist_v2.py).

E10. [Auditoria de eficiência histórica](https://github.com/Ricardojnf33/ChicoCienciaV1/blob/423875f03e0e6d63e921df852c57d4398e31236e/AUDITORIA_EFICIENCIA.md).

R1. Yamada, Y.; Lange, R. T.; Lu, C.; Hu, S.; Lu, C.; Foerster, J.; Clune, J.; Ha, D. The AI Scientist-v2: Workshop-Level Automated Scientific Discovery via Agentic Tree Search. 2025. [arXiv 2504.08066](https://arxiv.org/abs/2504.08066).

R2. Hevner, A. R.; March, S. T.; Park, J.; Ram, S. Design Science in Information Systems Research. MIS Quarterly, v. 28, n. 1, 2004. [Publicação na AIS eLibrary](https://aisel.aisnet.org/misq/vol28/iss1/6/).

R3. Scikit-learn. Nested versus non-nested cross-validation. [Documentação oficial](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html).
