# E00 — índice de evidências

Data: 27/09/2026. Status: gate documental remoto aprovado; G0 acadêmico e G2 E2E continuam pendentes.

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

## Evidência remota preservada

Workflow: `Roadmap E00 - manual evidence gate`; run [36350845233](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/36350845233), tentativa 1, disparado manualmente em `main` pelo responsável. Resultado: `success` no SHA `41857710afd66616423e80ce025f8ec676de7665`; job `validate-evidence` e suas etapas concluíram com sucesso.

O artifact `roadmap-e00-36350845233-1` (ID 10942187121; expira em 26/12/2026) foi baixado e seu SHA-256 conferido contra o digest retornado pela API. Cópias do `report.json`, `summary.md`, `checksums.json` e metadados da execução estão nesta pasta (`remote/`).

Os 11 checks de integridade documental passaram. O validador fez zero chamadas de LLM. Isso não valida a aplicação, não executa experimento/E2E, não reexecuta a Fase 5 e não encerra G0 acadêmico; G2 permanece `NOT_VALIDATED`.

## Limites e próximo passo

Sem alteração em src/, correção da Fase 5, experimento científico ou consumo pago. O gate documental remoto foi conferido e preservado; antes de E01, revisar e integrar manualmente o PR que registra esta evidência. Aguardar essa integração antes de abrir a próxima branch.
As informações acadêmicas pendentes estão em [PENDENCIAS_USUARIO.md](../../PENDENCIAS_USUARIO.md).
