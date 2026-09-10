# ADR 003 Escopo da contribuição e comparação experimental

Data: 10/09/2026. Status: proposta. Implementação prevista: Fases 4 e 5.

## Contexto

As métricas históricas não estabelecem descoberta científica autônoma, superioridade estatística de L2 nem ganho de produtividade de 23 vezes. Parte do desenho experimental precisa de correção.

## Decisão proposta

Avaliar confiabilidade, rastreabilidade e custo da orquestração no domínio de classificação com dados públicos. Comparar sequência B1 e árvore A com infraestrutura e ferramentas compartilhadas; usar B0 como referência convencional e A0 para estudar correção automática. Separar validade operacional de qualidade de ML.

## Alternativas e consequências

Expandir modelos e datasets sem corrigir o protocolo aumentaria volume sem resolver validade. Buscar uma descoberta inédita como condição de defesa criaria uma promessa sem evidência. O recorte proposto reduz generalização, mas permite perguntas mensuráveis e resultados negativos informativos.

## Evidência para aceitar a implementação

Protocolo congelado antes da coleta principal, contabilidade de todas as tentativas, ausência de ajustes seletivos e análise regenerável. Conclusões devem ser proporcionais ao desenho e ao tamanho da avaliação.
