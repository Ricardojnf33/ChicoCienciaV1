# Desenho acadêmico do mestrado

Status: proposta de pesquisa. Nenhuma nova avaliação live foi executada nesta entrega.

## 2 Problema de pesquisa e contribuição

### 2 1 Delimitação do problema

Em um workflow com modelos de linguagem, a saída de um agente pode parecer plausível e ainda ser inadequada para a próxima etapa. Um Researcher pode formular uma hipótese sem fonte verificável; um Coder pode gerar um script que não produz a métrica exigida; um Runner pode concluir sem preservar os arquivos; um Reviewer pode aprovar uma interpretação sem acesso aos dados corretos. A composição desses componentes exige contratos e verificações independentes do texto gerado.

A pergunta central será: em que medida contratos explícitos de resultados, execução controlada e persistência verificável melhoram a confiabilidade de um sistema multiagente de experimentação, e qual o custo adicional da busca em árvore em relação a uma orquestração sequencial?

O domínio fica restrito a experimentos pequenos de classificação supervisionada, em CPU, com datasets públicos e métricas previamente definidas. A generalização para descoberta científica em outros domínios dependerá de novos estudos.

### 2 2 Questões de pesquisa

| Questão | O que será investigado | Evidência necessária |
| --- | --- | --- |
| Q1 | A arquitetura identifica e registra falhas sem convertê-las em sucesso? | Casos de falha injetada, estados finais e artefatos de validação |
| Q2 | A busca em árvore entrega mais experimentos válidos por orçamento que a sequência fixa? | Runs pareados, sucesso válido, duração, tokens e intervenções |
| Q3 | A correção automática recupera falhas sem degradar a rastreabilidade? | Comparação com a variante sem correção e histórico de tentativas |
| Q4 | Um terceiro consegue reconstruir resultados e decisões a partir dos artefatos? | Reprodução a partir de checkout limpo e checklist independente |

### 2 3 Contribuições pretendidas

Pretendo entregar uma implementação de referência com contratos de execução e proveniência; um conjunto de testes de falhas derivado de problemas observados no protótipo; e uma avaliação empírica sobre os benefícios e custos da orquestração. A síntese de lições de projeto conectará cada decisão às evidências que a motivaram.

A originalidade será argumentada pela combinação e avaliação dessas decisões no contexto delimitado. Ela não decorre simplesmente de usar CrewAI, UCT ou vários agentes. O trabalho de Yamada et al. apresenta o AI Scientist-v2 e a busca agentiva progressiva como referência arquitetural; seus resultados pertencem àquele sistema e não são transferidos ao Chico Ciência. [R1]

## 5 Método de pesquisa

Adotarei Design Science Research como enquadramento para construir e avaliar um artefato que responde a um problema de engenharia. Hevner et al. relacionam a produção de conhecimento à construção e aplicação do artefato e à avaliação de sua utilidade. Neste projeto, operacionalizo esse enquadramento em diagnóstico, desenho, implementação, demonstração, avaliação e comunicação. Essa sequência é uma organização do trabalho proposta para o Chico Ciência. [R2]

O diagnóstico será sustentado pelo código, histórico, testes e artefatos do baseline. O desenho será registrado em decisões arquiteturais. A implementação ocorrerá em incrementos pequenos, cada um com critérios verificáveis. A avaliação combinará testes determinísticos de falhas com execuções controladas de agentes. A comunicação apresentará resultados favoráveis, desfavoráveis e inconclusivos.

O diário de desenvolvimento terá função de registro de decisões, não de instrumento isolado de validação. Para cada descoberta serão preservados o sintoma, a causa investigada, a mudança aplicada e o teste que a verifica. O pacote experimental final ligará as tabelas da dissertação aos dados brutos e aos scripts de análise.

Não usarei a simples passagem pelos estágios PRELIM, TUNING, RESEARCH_GRADE e ABLATIONS como evidência de qualidade acadêmica. Os nomes expressam intenção do workflow; a validade dependerá dos critérios de cada etapa. A estrutura e a formatação de submissão serão alinhadas às regras do programa e à orientação acadêmica, sem presumir que os documentos antigos constituam certificação de conformidade institucional.

## 12 Estrutura da dissertação

| Capítulo | Pergunta respondida | Material de apoio |
| --- | --- | --- |
| Introdução | Qual problema de engenharia motiva o trabalho? | Diagnóstico, escopo, questões e objetivos |
| Fundamentação | Quais conceitos sustentam as decisões? | Agentes, workflows, busca, proveniência e avaliação de artefatos |
| Método | Como o artefato e a avaliação foram conduzidos? | DSR, protocolo, medidas e ameaças à validade |
| Desenvolvimento | Como as descobertas modificaram o sistema? | Arquitetura, decisões, commits e testes |
| Avaliação | O que ocorreu nos experimentos? | Runs, falhas, custos, resultados e reprodução |
| Discussão | O que os resultados permitem concluir? | Respostas às questões e limites de generalização |
| Conclusão | Qual conhecimento e artefato foram entregues? | Contribuições demonstradas e trabalhos futuros |

Os capítulos de avaliação e conclusão serão atualizados com a coleta da Fase 5. Até lá, a escrita empregará o presente para fatos observados e o futuro para experimentos planejados. A dissertação distinguirá resultados do software, resultados dos modelos de ML e interpretações produzidas por agentes.

## 15 Riscos e limites da conclusão

O principal risco de validade interna é alterar várias partes entre B1 e A e atribuir o efeito à árvore. A implementação das variantes precisa compartilhar infraestrutura, contratos e ferramentas. Intervenções manuais devem ser registradas e contabilizadas; ajustes não registrados invalidam a comparação de autonomia.

A validade de construto depende de definir corretamente sucesso. Nenhuma métrica única resumirá qualidade científica, custo, rastreabilidade e segurança. A avaliação usará medidas separadas e conservará exemplos de falhas. Reviewer e VLM não serão tratados como árbitros infalíveis, e a avaliação não se apoiará exclusivamente em outro LLM.

A validade externa será limitada pelo tamanho e pela familiaridade dos datasets, pela dependência de modelo e pela execução em CPU. A avaliação não sustentará alegações sobre pesquisa médica, produção empresarial, descoberta científica inédita ou eliminação do pesquisador humano.

Mudanças de APIs, custo e disponibilidade podem afetar a coleta. Por isso, prompts, respostas, versões e horários serão registrados. O limite de prazo será tratado por redução de escopo antes da coleta, e não pela omissão de tentativas fracassadas. A banca deverá conseguir distinguir o alcance real da demonstração das extensões futuras.

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
