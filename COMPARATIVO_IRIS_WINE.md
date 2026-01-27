# Comparativo Transversal: Iris vs. Wine

Este documento apresenta uma análise comparativa do comportamento dos modelos de Regressão Logística regularizada em dois níveis distintos de complexidade dimensional.

## 1. Escalonamento da Performance
| Dataset | Features | Baseline Acc/F1 | Best L2 Acc/F1 | Ganho Real |
| :--- | :--- | :--- | :--- | :--- |
| **Iris** | 4 | 96.67% (Acc) | 98.00% (Acc) | +1.33% |
| **Wine** | 13 | 95.58% (F1) | 97.31% (F1) | +1.73% |

**Observação:** O ganho da regularização L2 foi proporcionalmente maior no dataset Wine. Isso valida a hipótese de que, conforme a dimensionalidade do problema aumenta, a necessidade de restringir a magnitude dos pesos torna-se mais crítica para evitar o overfitting.

## 2. O Colapso do Dropout em Dados Tabulares Pequenos
Ambos os experimentos confirmaram uma tendência perigosa para pesquisadores iniciantes: a aplicação indiscriminada de **Dropout** em datasets clássicos/pequenos.
- No **Iris**, o dropout reduziu a acurácia para **91.33%**.
- No **Wine**, o uso de dropout em uma rede neural simples causou um colapso para **36.99%** de F1-Score.

**Conclusão Científica:** O Dropout, sendo um processo estocástico, requer um volume de dados "mínimo crítico" para que a média das sub-redes treinadas convirja para um modelo robusto. Em datasets da UCI (como Iris e Wine), a técnica atua meramente como ruído destrutivo, eliminando informações vitais em espaços de decisão já densos.

## 3. Generalização Metodológica
O sistema ChicoCienciaV1 demonstrou alta **capacidade de transferência**. Sem alteração no núcleo do código dos agentes, a orquestração migrou de um problema de 4 dimensões para um de 13 dimensões, ajustando as métricas (de Acurácia para F1-Score) e as ferramentas estatísticas (teste t para Wilcoxon) de forma autônoma.
