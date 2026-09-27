# Documentação do mestrado sobre Chico Ciência

Autor: Ricardo Fernandes. Atualizado em 27/09/2026.

O objetivo desta documentação é transformar o diagnóstico do protótipo em um plano executável de conclusão do mestrado em Engenharia de Software. A contribuição proposta é a confiabilidade e a rastreabilidade da orquestração científica com agentes.

## Execução atual

- [Roadmap v1.1 em HTML](roadmap.html) e [backlog JSON](roadmap.json).
- [Acordo de execução e teste manual](EXECUCAO_ROADMAP.md).
- [Informações pendentes do responsável](PENDENCIAS_USUARIO.md).
- [Evidências E00](evidencias/e00-20260927/index.md).
- [Relatório final em construção](RELATORIO_FINAL.md).

## Leitura

- [Síntese e plano completo](SINTESE_E_PLANO.md)
- [Baseline auditado](BASELINE.md)
- [Rastreabilidade](RASTREABILIDADE.md)
- [Desenho acadêmico](DESENHO_ACADEMICO.md)
- [Protocolo de avaliação](PROTOCOLO_AVALIACAO.md)
- [Plano por fases](PLANO_FASES.md)
- [Relatório de encerramento da Fase 1](FASE_1_RELATORIO.md)
- [Relatório de encerramento da Fase 2](FASE_2_RELATORIO.md)
- [Relatório de encerramento da Fase 3](FASE_3_RELATORIO.md)
- [Relatório de encerramento da Fase 4](FASE_4_RELATORIO.md)
- [Runbook de execução e recuperação](RUNBOOK_RECUPERACAO.md)
- [Registro do processo](REGISTRO_PROCESSO.md)
- [Modelo de registro para próximas fases](MODELO_REGISTRO_FASE.md)
- [Decisão sobre contratos](decisoes/ADR_001_CONTRATOS.md)
- [Decisão sobre execução](decisoes/ADR_002_EXECUCAO.md)
- [Decisão sobre escopo](decisoes/ADR_003_ESCOPO.md)

## Estado real em 27/09/2026

Fases 1–4 integradas à main. A Fase 5 está implementada parcialmente na
[PR #7](https://github.com/Ricardojnf33/ChicoCienciaV1/pull/7), ainda aberta.
O preflight e a CI do SHA 03eaf5a passaram, mas o último piloto falhou:
[run 35047877307](https://github.com/Ricardojnf33/ChicoCienciaV1/actions/runs/35047877307).
B0, matriz e controles já existem nessa branch; não devem ser tratados como
pendentes de implementação na main sem considerar a PR.

E00 inicia o novo roadmap com integridade documental e execução manual pendente.
E2E, estudo empírico, melhoria recursiva e efeito do Jev não estão comprovados.
O replay de recuperação histórico não equivale ao replay de políticas proposto.
O protocolo antigo é preservado; a nova matriz precisa ser definida antes de
coleta adicional. A conclusão acadêmica depende também da orientação e programa.
