# Proposta de Estrutura de Dissertação (Template Metodológico)

Esta estrutura é baseada nas melhores práticas da CAPES para mestrados profissionais/acadêmicos em computação/IA no Brasil.

---

## 1. Introdução
- **1.1 Contextualização:** A evolução da descoberta científica automatizada (AI Scientists).
- **1.2 O Problema:** A dificuldade de explorar espaços de hipóteses complexos de forma reprodutível e rigorosa.
- **1.3 Objetivos:**
    - **Geral:** Implementar um sistema de Agentic Tree Search (ATS) para descoberta de modelos de ML.
    - **Específicos:** Integrar revisão de literatura automática, execução em sandbox e crítica visual via VLM.
- **1.4 Justificativa:** Aumento da produtividade do pesquisador e redução de viés humano.

## 2. Referencial Teórico (Estado da Arte)
- **2.1 LLMs na Ciência:** GPT-4, Claude e o estado da arte em agentes.
- **2.2 Orquestração de Agentes:** Frameworks como CrewAI e AutoGPT.
- **2.3 Busca em Árvore:** Algoritmos UCT e sua aplicação em espaços de decisão.
- **2.4 Revisão de Literatura Automática:** Uso de Semantic Scholar e ArXiv APIs.

## 3. Metodologia (ChicoCienciaV1)
- **3.1 Arquitetura do Sistema:** Descrição dos 4 estágios (PRELIM, TUNING, RESEARCH_GRADE, ABLATIONS).
- **3.2 Agentes Especializados:** Papéis e responsabilidades do Manager, Researcher, Coder, etc.
- **3.3 Ferramentas e Sandbox:** Como o código é gerado e executado com segurança.
- **3.4 O Algoritmo ATS:** Explicação da seleção UCT e backpropagação de scores.

## 4. Experimentos e Resultados
- **4.1 Configuração Experimental:** Uso do dataset Iris como prova de conceito.
- **4.2 Resultados Preliminares (PRELIM):** Hipóteses geradas pelos agentes.
- **4.3 Otimização (TUNING):** Busca de hiperparâmetros (C, dropout).
- **4.4 Resultados Rigorosos (RESEARCH_GRADE):** Análise do melhor nó (ex: d5068c16 com 97.8% de acurácia).

## 5. Análise e Discussão
- **5.1 Comparação com Literatura:** Como os achados do sistema se alinham com o conhecimento existente.
- **5.2 Validação VLM:** Eficácia da crítica visual na detecção de anomalias em gráficos.
- **5.3 Limitações:** Falhas semânticas em código (ex: penalty='none') e custo de API.

## 6. Conclusão
- **6.1 Contribuições:** Prova de conceito funcional de um "Cientista AI" autônomo.
- **6.2 Trabalhos Futuros:** Expansão para datasets maiores e integração com bases de dados privadas.

---

### Dica do R.J.:
Cada vez que eu (ou o sistema) gerar um relatório em `runs/`, você pode copiar as seções correspondentes para este template. O `STATUS_PROJETO.md` e o `DOCUMENTACAO_TECNICA.md` já fornecem o material base para os capítulos 3 e 4.
