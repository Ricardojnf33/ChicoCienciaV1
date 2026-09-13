# Rastreabilidade entre descobertas e entregas

Baseline: 423875f03e0e6d63e921df852c57d4398e31236e. D01 foi encerrada na Fase 1; D02, D03 e D04 foram encerradas na Fase 2. D07 recebeu o manifesto, mas continua aberta para atomicidade e retomada na Fase 3.

| Descoberta | Requisito | Decisão | Teste de aceitação planejado | Fase |
| --- | --- | --- | --- | --- |
| D01 CI não executa testes | RNF01 | Ambiente e lock coerentes | Concluído: lock validado, instalação limpa, lint e 4 testes offline aprovados no run 34509660031; `|| true` removido | 1 |
| D02 Métrica incompatível | RF03 | Contrato canônico | Concluído: três formatos históricos adaptados por caminho explícito, com valores preservados | 2 |
| D03 Arquivo tratado como sucesso | RF03 | Validar resultado e retorno | Concluído: retorno diferente de zero e resultado inválido não promovem o nó | 2 |
| D04 Fixture em modo real | RF02 | Modos separados | Concluído: live sem resultado é rejeitado; replay preserva origem; mock permanece sintético | 2 |
| D05 Avaliação presumida | RNF04 | Avaliação explícita | Reviewer ausente produz NOT_EVALUATED e não aprovação | 4 |
| D06 Filhos duplicados | RF05 | Hipótese estruturada | Filhos têm identificadores e planos distintos; duplicata é rejeitada | 4 |
| D07 Estado e evidência frágeis | RF04 e RF06 | Manifesto e checkpoint atômico | Parcial: manifesto rejeita duplicata; interrupção, atomicidade e retomada continuam na Fase 3 | 3 |
| D08 Rate limit por instância | RNF02 | Relógio e estado compartilhados | Duas instâncias respeitam o mesmo intervalo sem espera real no teste | 3 |
| Código sem isolamento reforçado | RNF03 | Runner restrito | Credenciais ausentes, rede bloqueada e timeout encerra processo | 3 |
| Wine com interpretação inadequada | RNF04 | Protocolo controlado | Predições são fora da amostra; coleta não usa o dropout histórico | 5 |

## Estado dos resultados

- Histórico: números versionados dos experimentos de 2025 e janeiro de 2026.
- Reprodução pontual: script Iris reexecutado na auditoria anterior; não é reprodução do workflow completo.
- Proposta: requisitos, desenho e matriz de 60 runs definidos nesta documentação.
- Concluído: ambiente e fluxo mock da Fase 1, sem execução live.
- Concluído: contratos, adaptação histórica, manifesto e validação de artefatos da Fase 2.
- Pendente: runner e recuperação, workflow multiagente, pilotos, coleta principal e revisão independente.

## Regra de encerramento

Para encerrar uma linha, adicionar caminho do teste, comando, revisão, resultado observado e referência ao artefato. Um campo preenchido por agente não substitui validação determinística quando esta é aplicável.
