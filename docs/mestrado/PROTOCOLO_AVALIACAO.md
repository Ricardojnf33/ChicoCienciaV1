# Protocolo de avaliação do Chico Ciência

Versão 0.1 proposta em 10/09/2026. Congelamento previsto após pilotos e antes da coleta principal. Ainda não pré-registrado nem executado.

## 8 Protocolo de avaliação proposto

### 8 1 Desenho comparativo

Compararei quatro condições sobre os mesmos objetivos. B0 servirá como controle de execução convencional; a comparação central sobre busca em árvore será entre B1 e A, que terão as mesmas ferramentas, modelos, corpus e regras de validação. A condição A0 removerá apenas a correção automática para investigar Q3.

| Condição | Descrição | Quantidade planejada |
| --- | --- | --- |
| B0 | Pipeline convencional com candidatos e execução definidos previamente | 3 datasets vezes 5 seeds igual a 15 runs |
| B1 | Agentes em sequência fixa, com correção limitada e sem árvore | 15 runs |
| A | Chico Ciência com árvore, validação e correção limitada | 15 runs |
| A0 | Mesma árvore e validação de A, sem correção automática | 15 runs |
| Total principal | 60 runs; 45 envolvem geração por LLM | 60 runs |

Os datasets propostos são Iris, Wine e Digits. As seeds de divisão serão 11, 23, 37, 51 e 71. Cada run é uma execução completa do workflow para uma condição, dataset e seed; não é um fold, um nó ou uma chamada de modelo. Temperatura, seed do provedor quando suportada e identificador do modelo serão registrados, sem pressupor determinismo de uma API externa.

Antes da coleta principal, farei seis runs piloto, dois por condição generativa, distribuídos entre Iris e Wine. Eles servirão para estimar viabilidade e ajustar limites. Seus dados serão excluídos da comparação principal. O protocolo será congelado em commit após o piloto. Qualquer ajuste posterior será registrado como desvio; não se escolherá uma configuração em função de favorecer A.

### 8 1 1 Execução automatizada das condições generativas

A Fase 4 implementou um manifesto comparativo que fixa o hash do objetivo e aplica a mesma configuração às três condições generativas. O smoke reproduzível, ainda sem LLM, é iniciado por:

```bash
poetry run python -m src.cli compare objective.example.yaml \
  --mode mock --budget 8 --branching 2 --max-depth 3 --max-branching 3
```

O comando executa B1, A e A0 em diretórios separados e registra a política efetiva. Na Fase 5, a troca para `--mode live` ocorrerá somente após os gates de sandbox, custo e congelamento. B0 e a expansão por datasets e seeds ainda serão materializados antes dos pilotos; portanto, este comando encerra o critério operacional da Fase 4, mas não constitui a coleta empírica.

### 8 2 Controle do orçamento e das condições

Como limite inicial a validar no piloto, cada run terá até seis tentativas de execução de candidato, no máximo duas correções por nó, 15 minutos de duração e 40 mil tokens totais registrados. Correções também consomem o limite de tentativas. O encerramento ocorrerá ao atingir qualquer teto. As condições generativas compartilharão esses limites; B0 terá o mesmo teto de avaliação de candidatos e registrará custo de LLM igual a zero.

Os 45 runs generativos principais mais seis pilotos representam um teto de planejamento de 2,04 milhões de tokens sob essa configuração. Esse valor não é consumo medido nem orçamento monetário. O valor financeiro será calculado a partir de tokens de entrada e saída, tarifas vigentes no início da coleta, infraestrutura e margem explicitada. O teto em moeda será registrado no manifesto da campanha antes da coleta paga.

O corpus bibliográfico será um snapshot comum, com identificadores e hashes. A ordem de execução das condições será alternada ou randomizada por dataset e seed, para reduzir efeitos de horário e instabilidade do serviço. Modelo, prompts, ferramentas e ambiente serão congelados. Uma mudança de versão do provedor exigirá nova identificação do lote.

### 8 3 Separação entre aprendizado de máquina e orquestração

A métrica principal da pesquisa de engenharia será a proporção de runs que terminam com experimento válido e rastreável. Acurácia e F1 macro serão métricas do experimento de aprendizado de máquina e permanecerão separadas do sucesso operacional. Um run com métrica modesta pode estar corretamente executado; um run com métrica elevada pode ser inválido.

Para cada seed, reservarei 20% dos dados para teste estratificado, inacessível aos agentes durante a seleção. Nos 80% restantes, usarei validação cruzada estratificada de cinco folds para comparar candidatos. Padronização e demais transformações serão ajustadas exclusivamente no treino de cada fold. O teste será executado uma vez para o candidato selecionado; seu resultado não retroalimentará a árvore. Essa decisão responde ao risco de viés quando seleção e avaliação reutilizam dados. [R3]

O conjunto de modelos ficará restrito a regressão logística e alternativas simples previamente declaradas. O baseline explicitará penalidade, solver e parâmetros. Dropout ficará fora da comparação principal: a implementação histórica do Wine será preservada como achado de auditoria. Uma extensão futura deverá implementar dropout no treinamento e definir o comportamento em avaliação antes de formular conclusões.

### 8 4 Medidas e análise

| Medida | Definição operacional | Uso |
| --- | --- | --- |
| Sucesso válido | Runs com execução e validação concluídas divididos por runs iniciados | Desfecho principal |
| Falso sucesso | Runs marcados como sucesso que violam o contrato | Falha crítica; alvo zero nos casos de teste |
| Completude | Runs com todos os campos e artefatos obrigatórios divididos pelo total | Rastreabilidade |
| Recuperação | Falhas injetadas recuperáveis corrigidas dentro dos limites | Comparação A versus A0 |
| Custo por sucesso | Custo total de todos os runs dividido por sucessos válidos | Eficiência sem ocultar tentativas fracassadas |
| Intervenção | Quantidade e tipo de ações humanas após início do run | Limite da autonomia |
| Qualidade de ML | Acurácia e F1 macro no teste reservado | Resultado secundário |

O denominador incluirá falhas, timeouts e esgotamento de orçamento. Se não houver sucessos, custo por sucesso será informado como indefinido, acompanhado do custo total. Registrarei contagens absolutas, proporções, diferenças pareadas, medianas de duração e distribuição dos custos.

Com apenas três datasets e cinco seeds por condição, a avaliação será tratada como estudo empírico delimitado. Os folds e splits reutilizam observações; não serão contados como amostras independentes para produzir significância artificial. Resultados serão apresentados por dataset. Intervalos descritivos de incerteza serão identificados como condicionais a esse desenho, e qualquer teste inferencial será definido antes da coleta com justificativa de suas premissas. Não haverá alegação ampla de superioridade baseada apenas em p-valor.

### 8 5 Testes de falhas e reprodução

A suíte determinística cobrirá resultado ausente, JSON malformado, métrica incorreta, valor NaN, artefato de outro run, timeout, exceção do runner, resposta inválida do agente, indisponibilidade bibliográfica, checkpoint interrompido, orçamento esgotado e tentativa duplicada. Cada caso terá estado esperado e verificações sobre arquivos e eventos. Fixtures e relógio controlado serão usados para evitar dependência de serviços externos.

Para Q4, um avaliador deverá executar o roteiro de reprodução em checkout limpo, verificar os hashes e reconstruir ao menos um resultado por dataset a partir de um pacote aceito. A identidade e o papel desse avaliador serão registrados quando a atividade ocorrer. Nenhuma avaliação independente será presumida a partir da execução realizada pelo próprio autor ou por ferramenta de assistência.

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
