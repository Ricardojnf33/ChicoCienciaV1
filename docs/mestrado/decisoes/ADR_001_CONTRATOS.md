# ADR 001 Contratos de resultado e sucesso verificado

Data: 10/09/2026. Status: proposta. Implementação prevista: Fase 2.

## Contexto

O baseline aceita a existência de código como indicação de sucesso e não consome os formatos aninhados dos resultados históricos no scorer. A ausência de arquivo pode acionar fallback sintético.

## Decisão proposta

Validar um modelo canônico de manifesto e resultado antes de promover um nó para SUCCEEDED. Manter modo mock, replay e live explícitos. Resultado ausente ou inválido não será convertido em métrica zero nem em simulação. Conservar formatos históricos com adaptadores identificados e sem alterar sua origem.

## Alternativas e consequências

Manter JSON livre reduziria trabalho inicial, mas preservaria a ambiguidade do contrato. Adotar esquema explícito exige migração e validação, em troca de erros observáveis e rastreabilidade. Os esquemas serão versionados e terão exemplos válidos e inválidos.

## Evidência para aceitar a implementação

Os testes de RF02 e RF03 passam; os casos de erro nunca terminam como sucesso; a métrica histórica adaptada mantém seu valor. A implementação será ligada ao commit e à CI no registro da Fase 2.
