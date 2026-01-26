# Metodologia: A Arquitetura do Sistema ChicoCienciaV1

A metodologia deste trabalho baseia-se na orquestração de uma comunidade de agentes de Inteligência Artificial para a execução do ciclo de descoberta científica. O processo foi estruturado em quatro camadas principais:

## 1. Agente Orquestrador (Manager)
O Agente Manager atua como o núcleo decisório estratégica, gerindo o "budget" de iterações e selecionando os ramos mais promissores na árvore de busca (Agentic Tree Search - ATS). Ele utiliza o algoritmo UCT (Upper Confidence Bound applied to Trees) para equilibrar a exploração de novas hipóteses com a exploração de caminhos que já demonstraram alta acurácia.

## 2. Camada de Pesquisa e Revisão (Researcher)
Responsável pelo levantamento do estado da arte, o agente Researcher utiliza ferramentas de busca em tempo real (Semantic Scholar e ArXiv). Para a iteração c7d345b0, o pesquisador identificou tendências recentes em regularização L2, permitindo que o plano experimental fosse desenhado com base em evidências bibliográficas reais, e não apenas em conhecimento prévio estático do modelo de linguagem.

## 3. Implementação e Execução (Coder & Runner)
O agente Coder traduz o plano experimental em código Python robusto e reprodutível. Durante esta pesquisa, foram implementados mecanismos de:
- **Fixação de Sementes (Seed Fixing):** Garantindo que o split de 5-fold cross-validation seja idêntico em todas as execuções.
- **Sandbox Execution:** O agente Runner executa o código em um ambiente controlado, capturando artefatos (results.json) e logs de erro para processos de *self-healing*.

## 4. Validação Crítica (Reviewer & VLM)
Após a geração dos resultados, o agente Reviewer analisa as métricas quantitativas, enquanto o VLM Critic (Vision-Language Model) analisa as figuras geradas (PNGs) para garantir que a representação visual dos dados está correta e livre de anomalias gráficas.
