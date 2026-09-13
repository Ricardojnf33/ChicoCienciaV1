# Rastreabilidade entre descobertas e entregas

Baseline: 423875f03e0e6d63e921df852c57d4398e31236e. A linha D01 foi implementada na Fase 1; as demais continuam como especificações até receberem evidência equivalente.

| Descoberta | Requisito | Decisão | Teste de aceitação planejado | Fase |
| --- | --- | --- | --- | --- |
| D01 CI não executa testes | RNF01 | Ambiente e lock coerentes | Concluído: lock validado, instalação limpa, lint e 4 testes offline aprovados no run 34509660031; `|| true` removido | 1 |
| D02 Métrica incompatível | RF03 | Contrato canônico | Resultado Iris adaptado preserva valor; chave errada é rejeitada | 2 |
| D03 Arquivo tratado como sucesso | RF03 | Validar resultado e retorno | Código existente com execução falha termina FAILED | 2 |
| D04 Fixture em modo real | RF02 | Modos separados | Ausência de resultado live nunca cria resultado sintético aceito | 2 |
| D05 Avaliação presumida | RNF04 | Avaliação explícita | Reviewer ausente produz NOT_EVALUATED e não aprovação | 4 |
| D06 Filhos duplicados | RF05 | Hipótese estruturada | Filhos têm identificadores e planos distintos; duplicata é rejeitada | 4 |
| D07 Estado e evidência frágeis | RF04 e RF06 | Manifesto e checkpoint atômico | Interrupção e retomada não duplicam tentativa concluída | 3 |
| D08 Rate limit por instância | RNF02 | Relógio e estado compartilhados | Duas instâncias respeitam o mesmo intervalo sem espera real no teste | 3 |
| Código sem isolamento reforçado | RNF03 | Runner restrito | Credenciais ausentes, rede bloqueada e timeout encerra processo | 3 |
| Wine com interpretação inadequada | RNF04 | Protocolo controlado | Predições são fora da amostra; coleta não usa o dropout histórico | 5 |

## Estado dos resultados

- Histórico: números versionados dos experimentos de 2025 e janeiro de 2026.
- Reprodução pontual: script Iris reexecutado na auditoria anterior; não é reprodução do workflow completo.
- Proposta: requisitos, desenho e matriz de 60 runs definidos nesta documentação.
- Concluído: ambiente e fluxo mock da Fase 1, sem execução live.
- Pendente: contratos da Fase 2, recuperação, workflow multiagente, pilotos, coleta principal e revisão independente.

## Regra de encerramento

Para encerrar uma linha, adicionar caminho do teste, comando, revisão, resultado observado e referência ao artefato. Um campo preenchido por agente não substitui validação determinística quando esta é aplicável.
