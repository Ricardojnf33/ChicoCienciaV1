# Modelo de registro de uma fase

Usar ao executar cada fase. Os campos descrevem o que deve ser registrado e não atestam execução.

| Campo | Conteúdo obrigatório |
| --- | --- |
| Identificação | Fase, data e responsável pela execução |
| Entrada | Commit de origem, problema e requisito |
| Mudança | Arquivos alterados e decisão arquitetural relacionada |
| Verificação | Comandos, ambiente, critérios esperados e resultado observado |
| Evidência | Logs sanitizados, caminho dos resultados e hashes |
| Limites | Falhas, pendências e intervenções humanas |
| Saída | Commit final e critérios satisfeitos ou não satisfeitos |
| Continuidade | Próxima ação concreta e dependências |

Estados permitidos: planejada, em execução, bloqueada, concluída. Uma fase só recebe concluída após registrar os critérios de saída e a evidência correspondente.
