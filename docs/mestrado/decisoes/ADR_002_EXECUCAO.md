# ADR 002 Execução controlada e persistência verificável

Data: 10/09/2026. Status: proposta. Implementação prevista: Fase 3.

## Contexto

O runner executa Python por subprocesso. O protótipo apresenta fragilidade nos caminhos, na persistência das tentativas e na validação da retomada.

## Decisão proposta

Executar código gerado em contêiner com credenciais removidas, usuário sem privilégios, recursos e tempo limitados, diretório por tentativa e rede bloqueada por padrão. Manter manifesto e eventos como evidência canônica e SQLite como projeção reconstruível. Gravar checkpoint de forma atômica após transições e no encerramento. Separar processo de decisão e processo de execução.

## Alternativas e consequências

Executar diretamente no host é simples, mas não atende ao isolamento definido para a versão acadêmica. Uma plataforma distribuída acrescentaria operação e custo fora do escopo. O contêiner local impõe requisitos de ambiente e deve ser testado; não garante isolamento absoluto contra qualquer código hostil.

## Evidência para aceitar a implementação

Teste de timeout, interrupção, retomada e tentativa duplicada; verificação de ausência de credenciais no runner e de limites; reconstrução da projeção SQLite a partir dos registros. A evidência deve apontar para o ambiente efetivamente usado.
