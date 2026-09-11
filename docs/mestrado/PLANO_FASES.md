# Plano por fases para conclusão do mestrado

Status em 10/09/2026: Fases 0, 1 e 2 concluídas com evidências; Fases 3 a 6 planejadas. Os encerramentos técnicos estão em [FASE_1_RELATORIO.md](FASE_1_RELATORIO.md) e [FASE_2_RELATORIO.md](FASE_2_RELATORIO.md).

## 6 Produto final e critérios de aceitação

O produto alvo será uma versão 1.0 acadêmica do Chico Ciência, executável localmente em CPU e acompanhada de uma demonstração com dados públicos. Essa identificação é uma meta de release; a versão atual continua 0.1.0.

| Requisito | Comportamento exigido | Critério observável |
| --- | --- | --- |
| RF01 | Inicializar, executar, inspecionar e retomar um run | O fluxo determinístico completo passa em checkout limpo |
| RF02 | Diferenciar mock, replay e live | Todo manifesto contém o modo; mock não entra em ranking live |
| RF03 | Validar o resultado antes de aceitá-lo | Arquivo ausente, inválido ou de outro nó nunca vira sucesso |
| RF04 | Preservar tentativas e decisões | Cada tentativa tem código, retorno, evidências e estado |
| RF05 | Criar hipóteses e filhos distinguíveis | Cada filho referencia hipótese própria ou é rejeitado como duplicata |
| RF06 | Restaurar execução interrompida | Nó concluído não é reexecutado nem contado duas vezes |
| RNF01 | Reproduzir ambiente e pipeline | Dependências e imagem identificadas; CI obrigatória passa |
| RNF02 | Limitar execução e custos | Timeout, limite de tentativas e orçamento encerram o processo |
| RNF03 | Restringir o runner | Código gerado não recebe credenciais nem rede por padrão |
| RNF04 | Auditar conclusões | Métricas e afirmações centrais apontam para artefatos ou referências |

A versão mínima inclui CLI, runner controlado, dados estruturados, testes, avaliação e documentação. O dashboard será uma camada de leitura e acompanhamento, integrada depois da estabilização do núcleo. Busca bibliográfica dinâmica, crítica visual avançada, múltiplos provedores, deployment público e treinamento de redes maiores serão extensões, salvo se sua ausência impedir responder às questões de pesquisa.

O encerramento acadêmico exige que o experimento seja realizado e analisado; não exige que a arquitetura proposta vença todos os baselines. Uma resposta negativa bem medida à Q2 continua sendo um resultado útil.

## 9 Plano de implementação por fases

As fases abaixo são unidades sequenciais de implementação. O estado e as evidências de cada fase são registrados individualmente; escrever o plano não basta para concluir uma etapa.

### Fase 0 Baseline e decisões

Consolidar o diagnóstico, a matriz de rastreabilidade, o escopo e o protocolo de avaliação. Preservar a revisão auditada e distinguir resultados históricos, reproduções pontuais e coleta futura. Registrar decisões sobre contrato, modos de execução e persistência.

Critério de saída: todas as alegações centrais apontam para uma fonte; o backlog liga achado, requisito, teste e entrega; o status real permanece identificável. A documentação produzida nesta etapa constitui o avanço atual do projeto.

### Fase 1 Ambiente e execução determinística

Estado: concluída. Evidência principal: GitHub Actions [run 34509660031](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34509660031), com instalação, lock, lint e testes aprovados.

Resolver a compatibilidade de Python e dependências com instalação limpa, escolhendo e mantendo um gerenciador e lock coerentes. Corrigir o import de JSON, os stubs e a seleção explícita de modo. Retirar a supressão de erros do pytest e separar testes unitários, de integração local e live.

Critério de saída: a CI instala, executa o lint no escopo definido e roda testes obrigatórios; o fluxo mock termina sem chave nem acesso à rede. Evidência: log da CI, lock, comandos e teste negativo que demonstra reprovação quando há erro.

### Fase 2 Contratos e estados

Estado: concluída. Evidência principal: schemas canônicos, 22 testes offline aprovados e GitHub Actions [run 34543573124](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34543573124).

Introduzir esquema de resultado e manifesto, adaptar métricas, validar artefatos e separar score de busca de resultado observado. Substituir sucesso por existência de arquivo por sucesso verificado. Criar diretório por run, nó e tentativa. Implementar estados explícitos e preservar resultados históricos sem misturá-los à nova coleta.

Critério de saída: nenhum caso de artefato inválido da suíte termina como sucesso; o scorer usa a métrica aceita; duplicatas são detectadas. Evidência: testes de contrato e exemplos válidos e inválidos.

### Fase 3 Runner e recuperação

Estado: concluída em código. Evidência principal: 32 testes offline aprovados, smoke mock com duas tentativas e [relatório da Fase 3](FASE_3_RELATORIO.md). Restrição: a prova positiva do namespace deve ocorrer em host Linux compatível antes dos pilotos; neste host o runner recusou a execução.

Implementar execução controlada, limites de recursos, encerramento de processos, checkpoint atômico, restauração idempotente e correção limitada. Corrigir o controle compartilhado do rate limiter e validar falhas de serviços com fixtures. Garantir que tentativas anteriores permaneçam consultáveis.

Critério de saída: falha injetada e reinício preservam o estado esperado; execução concluída não é repetida; timeout e orçamento encerram o trabalho; credenciais não aparecem no ambiente do runner. Evidência: logs, testes de isolamento e roteiro de recuperação.

### Fase 4 Busca e avaliação dos agentes

Estruturar hipóteses e planos, conectar filhos a decisões distintas, limitar profundidade e ramificação e testar seleção e propagação. Integrar resultados do Reviewer como dados verificáveis; representar VLM como não avaliado quando não houver avaliação confiável. Implementar B1, A e A0 com as mesmas ferramentas e limites.

Critério de saída: a execução mock cobre o ciclo completo com transições válidas; as variantes diferem apenas nos fatores planejados; o protocolo pode ser executado sem mudanças manuais durante o run.

### Fase 5 Avaliação empírica

Executar pilotos, congelar o protocolo, coletar os 60 runs principais e analisar falhas e resultados. Corrigir o desenho do Wine, preservar o conjunto de teste e medir custos e intervenções. Realizar a reprodução independente planejada.

Critério de saída: todas as tentativas previstas aparecem no registro; tabelas são regeneradas por script; desvios são documentados; Q1 a Q4 recebem resposta com limites explícitos. Uma hipótese não confirmada não impede o encerramento desta fase.

### Fase 6 Empacotamento e defesa

Integrar ou simplificar o dashboard, fornecer quickstart, exemplo reproduzível, relatório, demonstração gravada e roteiro de defesa. Revisar texto e referências, confrontar cada alegação com a evidência e publicar a versão final apenas após os critérios técnicos e acadêmicos aplicáveis.

Critério de saída: uma pessoa com acesso ao pacote consegue executar o exemplo e reconstruir as tabelas; a versão do código coincide com a dissertação; a apresentação diferencia contribuição, resultados e limitações.

## 10 Cronograma e prioridades

Planejo oito semanas a partir do início efetivo da implementação, com dedicação de referência de 12 a 16 horas por semana. Essa é uma estimativa de planejamento de 96 a 128 horas, que será revisada após a Fase 1 e os pilotos; não é uma data de defesa nem uma promessa de duração.

| Janela | Foco | Entrega principal |
| --- | --- | --- |
| Semana 1 | Fases 0 e 1 | Baseline registrado e CI funcional |
| Semana 2 | Fase 2 | Contratos, estados e artefatos |
| Semanas 3 e 4 | Fases 3 e 4 | Recuperação e workflow validado |
| Semana 5 | Fase 5 inicial | Pilotos e protocolo congelado |
| Semana 6 | Fase 5 principal | Coleta e análise |
| Semana 7 | Fase 6 | Texto, pacote e demonstração |
| Semana 8 | Revisão e reserva | Reprodução externa e ajustes da defesa |

Se houver restrição de prazo, a prioridade será manter contratos, execução controlada, comparação B1 versus A e documentação dos resultados. Serão reduzidos primeiro o acabamento do dashboard e as extensões de VLM, corpus dinâmico e provedores. Uma redução da matriz experimental deverá ocorrer antes da coleta principal e ser declarada como alteração do protocolo, com a limitação correspondente.

## 11 Versionamento e documentação contínua

Cada fase deverá produzir commits pequenos e um registro de encerramento. Um commit representa uma mudança rastreável, não uma validação automática. Os documentos serão mantidos em `docs/mestrado/`, com decisões em `decisoes/` e evidências referenciadas por caminho e hash.

| Fase | Sequência sugerida de commits | Evidência de encerramento |
| --- | --- | --- |
| 0 | docs baseline; docs escopo; docs protocolo | Matriz de rastreabilidade revisada |
| 1 | fix dependências; fix modo mock; ci testes obrigatórios | CI verde e instalação limpa |
| 2 | feat schemas; fix validação; test contratos | Artefatos inválidos rejeitados |
| 3 | feat runner; fix checkpoint; test recuperação | Falhas controladas e retomada |
| 4 | feat hipóteses; fix árvore; test variantes | Ciclo completo e diferenças controladas |
| 5 | experiment piloto; docs protocolo congelado; experiment avaliação | Dados brutos e análise regenerável |
| 6 | docs dissertação; docs demo; chore versão final | Pacote revisado e demonstração |

O registro de uma fase conterá objetivo, revisão de entrada, arquivos alterados, comandos executados, resultado esperado, resultado observado, limitações, decisões, revisão de saída e próxima ação. Falhas terão descrição e evidência preservadas. Logs com dados sensíveis serão sanitizados antes de versionar.

Para cada requisito, o revisor poderá percorrer a relação descoberta, decisão, implementação, teste e resultado. A atualização da dissertação acompanhará o encerramento das fases, evitando reconstruir retrospectivamente justificativas que não foram registradas.

Na entrega documental atual, os commits serão organizados em três incrementos: diagnóstico e rastreabilidade; desenho acadêmico e decisões; síntese, plano e roteiro de apresentação. As fases de implementação 1 a 6 continuam planejadas. O histórico desta documentação será consultável na branch dedicada e no registro de execução que acompanha este documento.

## 16 Condições para encerrar o projeto

Considerarei a versão técnica pronta para defesa quando o ambiente for reproduzível; a CI obrigatória passar; os casos críticos de falso sucesso forem rejeitados; o ciclo completo e a retomada forem demonstrados; o orçamento limitar a execução; e os resultados forem associados a artefatos verificáveis.

Considerarei a avaliação concluída quando a matriz planejada, ou sua revisão previamente registrada, tiver sido executada; todas as tentativas estiverem contabilizadas; as tabelas puderem ser regeneradas; e as questões de pesquisa receberem respostas proporcionais à evidência. A reprodução independente terá seu resultado registrado, inclusive em caso de dificuldade.

Considerarei a comunicação concluída quando dissertação, código e demonstração apontarem para a mesma revisão; as referências estiverem verificadas; e o texto não atribuir validade, autonomia ou superioridade além do que foi observado. O orientador e o programa determinarão os requisitos formais da submissão e da defesa.
