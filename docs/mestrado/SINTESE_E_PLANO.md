# Chico Ciência como sistema multiagente para experimentação rastreável

Síntese do desenvolvimento e plano de conclusão do mestrado em Engenharia de Software

Ricardo Fernandes

10 de setembro de 2026

## 1 Síntese executiva

Desenvolvi o Chico Ciência para explorar a organização de tarefas de pesquisa em aprendizado de máquina por agentes especializados. A arquitetura combina planejamento, consulta bibliográfica, geração de código, execução, revisão e busca em árvore. Ao investigar o comportamento do protótipo, identifiquei que a confiabilidade depende da ligação verificável entre essas etapas. Um arquivo de código existente, uma mensagem de sucesso ou um score elevado não demonstram, isoladamente, que um experimento válido ocorreu.

A principal descoberta de engenharia foi a fragilidade do contrato entre intenção, execução e evidência. O protótipo consegue representar um ciclo científico e contém scripts experimentais reproduzíveis, mas ainda permite que resultados ausentes, estruturas de dados incompatíveis e avaliações presumidas influenciem o estado da pesquisa. Essa descoberta orienta a contribuição proposta para o mestrado: projetar e avaliar uma arquitetura de orquestração multiagente que torne falhas observáveis e preserve a rastreabilidade dos resultados.

O baseline documental é a revisão `423875f03e0e6d63e921df852c57d4398e31236e` da branch `main`. A auditoria de 10/09/2026 encontrou 18 execuções de integração contínua com conclusão de falha. A mais recente parou na instalação das dependências. Um experimento Iris foi reproduzido isoladamente na investigação, recuperando 96,67% de acurácia no baseline e 98,00% na melhor configuração de L2. O ciclo completo com agentes permanece sem validação reproduzível de ponta a ponta. [E1–E5]

Proponho encerrar o projeto com um artefato instalável, um protocolo experimental congelado, uma avaliação comparativa e uma demonstração auditável. O sucesso acadêmico dependerá da qualidade da construção e da avaliação, inclusive se a busca em árvore não superar uma execução sequencial. As metas e experimentos descritos a seguir são trabalho planejado; os resultados históricos permanecem identificados como tal.

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

## 5 Método de pesquisa

Adotarei Design Science Research como enquadramento para construir e avaliar um artefato que responde a um problema de engenharia. Hevner et al. relacionam a produção de conhecimento à construção e aplicação do artefato e à avaliação de sua utilidade. Neste projeto, operacionalizo esse enquadramento em diagnóstico, desenho, implementação, demonstração, avaliação e comunicação. Essa sequência é uma organização do trabalho proposta para o Chico Ciência. [R2]

O diagnóstico será sustentado pelo código, histórico, testes e artefatos do baseline. O desenho será registrado em decisões arquiteturais. A implementação ocorrerá em incrementos pequenos, cada um com critérios verificáveis. A avaliação combinará testes determinísticos de falhas com execuções controladas de agentes. A comunicação apresentará resultados favoráveis, desfavoráveis e inconclusivos.

O diário de desenvolvimento terá função de registro de decisões, não de instrumento isolado de validação. Para cada descoberta serão preservados o sintoma, a causa investigada, a mudança aplicada e o teste que a verifica. O pacote experimental final ligará as tabelas da dissertação aos dados brutos e aos scripts de análise.

Não usarei a simples passagem pelos estágios PRELIM, TUNING, RESEARCH_GRADE e ABLATIONS como evidência de qualidade acadêmica. Os nomes expressam intenção do workflow; a validade dependerá dos critérios de cada etapa. A estrutura e a formatação de submissão serão alinhadas às regras do programa e à orientação acadêmica, sem presumir que os documentos antigos constituam certificação de conformidade institucional.

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

## 7 Arquitetura alvo

### 7 1 Separação de responsabilidades

| Componente | Responsabilidade | Restrição |
| --- | --- | --- |
| Orquestrador | Aplicar estados, orçamento, seleção e transições | Não aceitar texto livre como prova de execução |
| Agentes | Propor hipóteses, código e interpretações | Responder em contratos validados |
| Runner | Executar código em ambiente controlado | Acesso mínimo, limites e retorno estruturado |
| Validador | Conferir esquema, métrica e vínculo dos arquivos | Decisão independente da avaliação verbal do agente |
| Registro de evidências | Preservar manifesto, eventos, hashes e referências | Escritas atômicas e histórico por tentativa |
| Relatório e interface | Exibir estado e resultados aceitos | Informar ausência de avaliação e intervenção humana |

### 7 2 Contrato de evidência

O manifesto de run terá `schema_version`, `run_id`, `mode`, commit de origem, hash do objetivo, modelo e parâmetros, identificação do ambiente, orçamento, timestamps e estado. Cada tentativa terá `node_id`, `hypothesis_id`, `attempt_id`, hash do código, retorno do runner, duração, caminhos relativos e hashes dos artefatos.

O resultado validado terá nome, direção e valor da métrica; dataset e hash dos dados; seed e identificação dos splits; predições de avaliação; avisos; e a decisão do validador. Valores não finitos e chaves ausentes serão rejeitados ou representados por ausência explícita, nunca convertidos silenciosamente em zero. Os números históricos não serão reescritos para parecerem parte do novo protocolo.

Um nó percorrerá estados como PENDING, PLANNED, CODE_READY, RUNNING, VALIDATING e SUCCEEDED. FAILED, TIMEOUT, CANCELLED e BUDGET_EXCEEDED serão terminais ou recuperáveis conforme política registrada. A transição para SUCCEEDED exigirá retorno zero, resultado válido, artefatos associados à tentativa correta e verificações do protocolo experimental.

### 7 3 Decisões técnicas propostas

Preservarei CrewAI atrás de uma interface de adaptação, evitando refazer o sistema antes de medir a necessidade. O modo mock terá contratos idênticos aos do modo live, mas implementação própria. O replay reproduzirá respostas registradas e não será descrito como nova execução autônoma. O runner receberá apenas dados e parâmetros necessários; consultas bibliográficas ocorrerão fora dele.

O runner utilizará processo isolado em contêiner com usuário sem privilégios, diretório de trabalho por tentativa, limites de CPU, memória, processos e tempo, filesystem restrito e rede desativada por padrão. Essa configuração reduz a superfície de risco no escopo da demonstração; não será apresentada como garantia absoluta contra código hostil.

O score só considerará nós com resultados válidos. Inicialmente, a seleção usará a métrica de validação dentro do orçamento; novidade bibliográfica e concordância visual serão indicadores separados, até possuírem avaliação confiável. O teste final ficará inacessível à seleção. A propagação da busca será mantida separada da métrica observada do próprio nó, evitando atribuir a um ancestral a qualidade experimental de um descendente.

O checkpoint será gravado atomicamente após cada transição relevante e no encerramento, inclusive por limite ou parada antecipada. JSON e eventos formarão a fonte canônica inicial; SQLite será uma projeção reconstruível para consulta. Uma migração documentada preservará os registros antigos.

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

## 9 Plano de implementação por fases

As fases abaixo são unidades de implementação futura. A documentação desta entrega organiza o trabalho, mas não marca as correções ou a avaliação como concluídas.

### Fase 0 Baseline e decisões

Consolidar o diagnóstico, a matriz de rastreabilidade, o escopo e o protocolo de avaliação. Preservar a revisão auditada e distinguir resultados históricos, reproduções pontuais e coleta futura. Registrar decisões sobre contrato, modos de execução e persistência.

Critério de saída: todas as alegações centrais apontam para uma fonte; o backlog liga achado, requisito, teste e entrega; o status real permanece identificável. A documentação produzida nesta etapa constitui o avanço atual do projeto.

### Fase 1 Ambiente e execução determinística

Resolver a compatibilidade de Python e dependências com instalação limpa, escolhendo e mantendo um gerenciador e lock coerentes. Corrigir o import de JSON, os stubs e a seleção explícita de modo. Retirar a supressão de erros do pytest e separar testes unitários, de integração local e live.

Critério de saída: a CI instala, executa o lint no escopo definido e roda testes obrigatórios; o fluxo mock termina sem chave nem acesso à rede. Evidência: log da CI, lock, comandos e teste negativo que demonstra reprovação quando há erro.

### Fase 2 Contratos e estados

Introduzir esquema de resultado e manifesto, adaptar métricas, validar artefatos e separar score de busca de resultado observado. Substituir sucesso por existência de arquivo por sucesso verificado. Criar diretório por run, nó e tentativa. Implementar estados explícitos e preservar resultados históricos sem misturá-los à nova coleta.

Critério de saída: nenhum caso de artefato inválido da suíte termina como sucesso; o scorer usa a métrica aceita; duplicatas são detectadas. Evidência: testes de contrato e exemplos válidos e inválidos.

### Fase 3 Runner e recuperação

Estado em 11/09/2026: concluída em código, com 32 testes offline, smoke mock e GitHub Actions [34553951163](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34553951163) aprovados. O live falha fechado quando o host não permite o namespace; a prova positiva em host compatível é requisito pré-piloto. Ver [relatório](FASE_3_RELATORIO.md) e [runbook](RUNBOOK_RECUPERACAO.md).

Implementar execução controlada, limites de recursos, encerramento de processos, checkpoint atômico, restauração idempotente e correção limitada. Corrigir o controle compartilhado do rate limiter e validar falhas de serviços com fixtures. Garantir que tentativas anteriores permaneçam consultáveis.

Critério de saída: falha injetada e reinício preservam o estado esperado; execução concluída não é repetida; timeout e orçamento encerram o trabalho; credenciais não aparecem no ambiente do runner. Evidência: logs, testes de isolamento e roteiro de recuperação.

### Fase 4 Busca e avaliação dos agentes

Estado em 11/09/2026: concluída com 50 testes offline, smoke comparativo B1/A/A0 e GitHub Actions [34617850898](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/34617850898) aprovados. Nenhuma chamada de LLM foi realizada. Ver [relatório](FASE_4_RELATORIO.md).

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

## 13 Síntese autoral para a apresentação

### 13 1 Abertura sustentada pelo estado atual

Neste trabalho, investiguei como organizar tarefas de experimentação em aprendizado de máquina por meio de um sistema multiagente. O Chico Ciência reúne agentes de pesquisa, programação, execução e revisão, coordenados por uma estrutura de busca em árvore. Meu interesse de engenharia está em transformar essa coordenação em um processo cujo resultado possa ser inspecionado e reproduzido.

Durante o desenvolvimento, identifiquei um problema que passou a orientar o projeto: o sistema podia avançar mesmo sem evidência suficiente de que a etapa anterior havia sido concluída corretamente. A presença de um arquivo de código podia ser aceita como sucesso, e o formato de resultados nem sempre correspondia ao esperado pelo cálculo do score. Esse comportamento compromete a interpretação do progresso e a comparação entre experimentos.

Os artefatos existentes mostram que é possível executar experimentos pequenos e recuperar seus resultados. Na reprodução do script Iris feita durante a auditoria, os principais números foram recuperados. Contudo, isso não estabelece a confiabilidade do ciclo completo com agentes. Também identifiquei limites na interpretação estatística e na implementação experimental do Wine.

A partir dessas descobertas, proponho uma arquitetura baseada em contratos de resultado, estados explícitos, execução controlada e registro de evidências. A avaliação comparará a busca em árvore com uma sequência fixa sob orçamento equivalente e medirá sucesso válido, recuperação de falhas, custo e intervenção humana.

A contribuição que busco apresentar é um entendimento verificável das condições em que esse tipo de sistema pode apoiar a experimentação. A versão final deverá mostrar o que funciona, onde falha, quanto custa e quais decisões de projeto explicam esse comportamento.

### 13 2 Conclusão que já pode ser defendida

O desenvolvimento do Chico Ciência permitiu identificar que a confiabilidade de um workflow científico com agentes depende da verificação das transições entre planejamento, código, execução e interpretação. Os experimentos históricos oferecem evidência de capacidade operacional localizada; a auditoria revelou lacunas que impedem extrapolar essa evidência para autonomia e validade científica do sistema completo.

Concluo, no estágio atual, que a contribuição mais consistente para o mestrado está em construir e avaliar mecanismos que preservem essas distinções. A arquitetura e o protocolo aqui definidos estabelecem um caminho verificável para a conclusão. A afirmação de melhoria de confiabilidade ou eficiência será feita somente após a avaliação comparativa, acompanhada dos resultados e das limitações observadas.

## 14 Roteiro da defesa final

O roteiro pressupõe 20 minutos de apresentação. Os números da coleta futura serão inseridos apenas após a Fase 5. Uma demonstração em replay será identificada como replay; uma execução ao vivo mostrará seu modo, orçamento e estado.

| Parte | Mensagem principal | Tempo |
| --- | --- | --- |
| 1 Tema e problema | Por que a confiança no workflow precisa de evidência | 1 minuto |
| 2 Contexto técnico | Como o Chico Ciência organiza os agentes | 2 minutos |
| 3 Descobertas | Quais falhas motivaram o redesenho | 2 minutos |
| 4 Questões e método | O que foi perguntado e como foi avaliado | 2 minutos |
| 5 Arquitetura | Contratos, estados, runner e proveniência | 3 minutos |
| 6 Demonstração | Um run, uma falha e uma retomada | 3 minutos |
| 7 Resultados | Comparação de sucesso, custo e recuperação | 3 minutos |
| 8 Limitações | Onde a evidência não permite generalizar | 2 minutos |
| 9 Contribuições e conclusão | O que foi aprendido e entregue | 2 minutos |

Na demonstração, abrirei um objetivo conhecido, exibirei uma hipótese e seu código, mostrarei o resultado validado e o vínculo com o manifesto. Em seguida, exibirei um caso de falha controlada e sua retomada. O foco será a evidência da transição de estados; o tempo de espera de uma API não deverá consumir a defesa.

Para a pergunta sobre autonomia, responderei com a quantidade de intervenções registradas e os limites das ferramentas. Para a pergunta sobre novidade, apresentarei a lacuna e a avaliação do artefato. Para a pergunta sobre uma eventual ausência de ganho da árvore, mostrarei o custo adicional e a conclusão correspondente. Para a pergunta sobre reprodutibilidade, distinguirei execução do mesmo código, replay e nova geração pelo modelo.

## 15 Riscos e limites da conclusão

O principal risco de validade interna é alterar várias partes entre B1 e A e atribuir o efeito à árvore. A implementação das variantes precisa compartilhar infraestrutura, contratos e ferramentas. Intervenções manuais devem ser registradas e contabilizadas; ajustes não registrados invalidam a comparação de autonomia.

A validade de construto depende de definir corretamente sucesso. Nenhuma métrica única resumirá qualidade científica, custo, rastreabilidade e segurança. A avaliação usará medidas separadas e conservará exemplos de falhas. Reviewer e VLM não serão tratados como árbitros infalíveis, e a avaliação não se apoiará exclusivamente em outro LLM.

A validade externa será limitada pelo tamanho e pela familiaridade dos datasets, pela dependência de modelo e pela execução em CPU. A avaliação não sustentará alegações sobre pesquisa médica, produção empresarial, descoberta científica inédita ou eliminação do pesquisador humano.

Mudanças de APIs, custo e disponibilidade podem afetar a coleta. Por isso, prompts, respostas, versões e horários serão registrados. O limite de prazo será tratado por redução de escopo antes da coleta, e não pela omissão de tentativas fracassadas. A banca deverá conseguir distinguir o alcance real da demonstração das extensões futuras.

## 16 Condições para encerrar o projeto

Considerarei a versão técnica pronta para defesa quando o ambiente for reproduzível; a CI obrigatória passar; os casos críticos de falso sucesso forem rejeitados; o ciclo completo e a retomada forem demonstrados; o orçamento limitar a execução; e os resultados forem associados a artefatos verificáveis.

Considerarei a avaliação concluída quando a matriz planejada, ou sua revisão previamente registrada, tiver sido executada; todas as tentativas estiverem contabilizadas; as tabelas puderem ser regeneradas; e as questões de pesquisa receberem respostas proporcionais à evidência. A reprodução independente terá seu resultado registrado, inclusive em caso de dificuldade.

Considerarei a comunicação concluída quando dissertação, código e demonstração apontarem para a mesma revisão; as referências estiverem verificadas; e o texto não atribuir validade, autonomia ou superioridade além do que foi observado. O orientador e o programa determinarão os requisitos formais da submissão e da defesa.

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
