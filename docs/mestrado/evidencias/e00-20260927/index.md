# E00 — índice de evidências

Data: 27/09/2026. Status: preparado; execução manual remota PENDENTE.

## Estado observado

[Snapshot estruturado](baseline.json) registra fontes API, SHAs, PRs e runs.
Main: `4ba97396dcc02aa53d2da4a3365c463df313ce5d`.
Fase 5: `03eaf5a850f7bbb4ce8fbaf9d9f120517edf4d10`, [PR #7](https://github.com/Ricardojnf33/ChicoCienciaV1/pull/7) aberta.

A consulta da árvore não encontrou AGENTS.md nessa baseline. As regras novas de
execução estão em [EXECUCAO_ROADMAP.md](../../EXECUCAO_ROADMAP.md).

- [Último piloto](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35047877307): failure.
- [CI do mesmo SHA](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35047282318): success.
- [Preflight do mesmo SHA](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35047282261): success.
- Diagnóstico observado anteriormente nos logs do piloto: mensagem de limite
  materializada como Python; a causa de atingir o limite permanece a investigar.

## Validação deste incremento

- Validador: `scripts/validate_roadmap.py` (stdlib; zero chamadas de modelo).
- [Relatório local](local/report.json) e [checksums locais](local/checksums.json).
- Valida arquivos obrigatórios, IDs, âncoras, paridade HTML/JSON, dependências,
  ausência de ciclo entre histórias e presença dos requisitos de monitoramento.
- [Casos negativos do validador](local/regression.md): ciclo e arquivo ausente recusados.
- Não executa a aplicação, não certifica G2 e não faz validação visual do HTML.
- O relatório identifica LOCAL_WORKING_TREE; não equivale a um run remoto.

## Evidência remota aguardada

Workflow: `Roadmap E00 - manual evidence gate`.
Após merge manual, disparar em main com `VALIDAR_E00_SEM_LLM`.
O próximo registro deve conter URL/id/attempt do run, SHA testado, conclusão,
nome/id do artifact, report.json e checksums.json preservados antes de expirar.
O workflow só valida integridade documental; não encerra G0 acadêmico.

## Limites e próximo passo

Sem alteração em src/, sem correção da Fase 5, sem dispatch e sem consumo pago
neste incremento. Aguardar usuário executar e conferir o resultado antes de E01.
As informações acadêmicas pendentes estão em [PENDENCIAS_USUARIO.md](../../PENDENCIAS_USUARIO.md).
