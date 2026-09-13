# ADR 002 Execução controlada e persistência verificável

Data: 10/09/2026. Decisão revisada e aceita com restrição operacional em 11/09/2026. Implementação: Fase 3.

## Contexto

O runner executa Python por subprocesso. O protótipo apresenta fragilidade nos caminhos, na persistência das tentativas e na validação da retomada.

## Decisão

Executar código gerado fora do processo decisório, em namespace Linux Bubblewrap com capabilities removidas, credenciais removidas, recursos e tempo limitados, filesystem mínimo, diretório gravável por tentativa e rede separada por padrão. Se o namespace não puder ser criado, falhar antes do código. Manter manifesto e árvore como evidência canônica e SQLite como projeção reconstruível. Gravar arquivos críticos por troca atômica e reconciliar a janela entre manifesto e árvore de forma idempotente.

## Alternativas e consequências

Executar diretamente no host é simples, mas não atende ao isolamento definido para a versão acadêmica. Uma plataforma distribuída ou uma imagem de contêiner acrescentaria operação, distribuição de imagem e custo fora do escopo. O namespace local reutiliza o ambiente Python travado, exige Bubblewrap e permissões do kernel e não garante isolamento absoluto contra qualquer código hostil.

## Evidência para aceitar a implementação

Testes de timeout, interrupção, retomada, tentativa duplicada, ausência de credenciais, limites, filesystem mínimo e reconstrução SQLite foram aprovados. A aceitação operacional exige ainda um smoke positivo do namespace em host compatível antes dos pilotos. O host de desenvolvimento atual negou namespaces, e o runner recusou a execução como definido.
