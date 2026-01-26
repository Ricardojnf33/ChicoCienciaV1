# Roadmap Metodológico para Mestrado (Brasil - Padrão CAPES)

Este documento mapeia o funcionamento técnico do **ChicoCienciaV1** para a estrutura formal de uma dissertação de mestrado, garantindo que cada iteração do agente produza material útil para a escrita acadêmica.

---

## 1. Mapeamento de Estágios ATS vs. Estrutura da Dissertação

| Estágio do Agente | Fase da Pesquisa | Conteúdo Gerado para a Tese |
| :--- | :--- | :--- |
| **PRELIM** | **Introdução / Estado da Arte** | Formulação do Problema, Hipóteses Iniciais, Levantamento Bibliográfico (via LiteratureTool). |
| **TUNING** | **Desenvolvimento / Testes Preliminares** | Design Experimental, Justificativa de Hiperparâmetros, Baselines. |
| **RESEARCH_GRADE** | **Resultados e Discussão** | Experimentos Rigorosos, Validação Estatística, Análise de Coerência (via VLM Critic). |
| **ABLATIONS** | **Análise de Sensibilidade / Conclusão** | Testes de Robustez, Identificação de Componentes Críticos, Limitações do Estudo. |

---

## 2. Padrões de Qualidade (Metodologia Científica)

Para que a iteração seja considerada "completa" e válida para o padrão brasileiro:

1.  **Reprodutibilidade (Rigor):**
    -   Todo código deve usar `seed` fixo (já implementado no `DatasetTool`).
    -   Logs devem registrar as versões das bibliotecas e parâmetros exatos.
2.  **Referencial Teórico (Literature):**
    -   As buscas via **Semantic Scholar** devem focar em periódicos de alto impacto (Qualis A).
    -   O Researcher deve contrastar as hipóteses com o que já foi publicado.
3.  **Visualização (Evidence):**
    -   Figuras devem seguir padrões de publicação (eixos nomeados, legendas, alta resolução).
    -   O `VLM Critic` atua como um "revisor cego", garantindo que a figura não contenha erros visuais óbvios.

---

## 3. Protocolo de "Iteração Completa Sem Quebras"

Para atingir o objetivo de uma execução estável:

-   **Orquestração em Loop:** O sistema usa um mecanismo de *Self-Healing* (implementado em `ats_process.py`) que tenta corrigir o código caso o `Runner` falhe.
-   **Consistência de Dados:** Todos os artefatos são salvos em pastas únicas por nó (`experiments/{node_id}/`), evitando sobrescrita.
-   **Persistência:** O estado da árvore é salvo em SQLite e JSON, permitindo retomar a pesquisa de qualquer ponto em caso de falha catastrófica.

---

## 4. Próximos Passos Acadêmicos

1.  **Definição do Baseline:** Executar o nó raiz para estabelecer o desempenho atual sem as melhorias propostas.
2.  **Expansão da Literatura:** Cruzar os resultados obtidos com os papers retornados pelo Semantic Scholar para construir o capítulo de "Discussão".
3.  **Redação Automática:** Usar os relatórios gerados em `runs/*.md` como rascunhos para as seções de Metodologia e Resultados.

---
**Status da Metodologia:** 🟢 Alinhada com os requisitos de Mestrado.
**Próxima Meta:** Execução do primeiro ciclo REAL com budget total.
