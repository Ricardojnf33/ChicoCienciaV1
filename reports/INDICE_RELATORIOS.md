# Índice de Relatórios - Teste Ao Vivo ChicoCienciaV1

**Data**: 2025-11-08  
**Run ID**: `70f8222b`

---

## Relatórios Disponíveis

### 1. Relatório Executivo Completo

**Arquivo**: `RELATORIO_EXECUTIVO_TESTE_AO_VIVO.md`

**Conteúdo**:
- Sumário executivo detalhado
- Métricas de performance completas
- Análise de logs e eventos
- Validações realizadas
- Recomendações e próximos passos

**Uso**: Documento principal para stakeholders e gestão

---

### 2. Relatório Técnico JSON

**Arquivo**: `live_test_70f8222b_20251108_175928.json`

**Conteúdo**:
- Métricas brutas em formato JSON
- Logs completos estruturados
- Estatísticas detalhadas
- Dados para análise programática

**Uso**: Análise automatizada, integração com ferramentas

---

### 3. Relatório Markdown Resumido

**Arquivo**: `live_test_70f8222b_20251108_175928.md`

**Conteúdo**:
- Sumário executivo
- Métricas principais
- Conclusão rápida

**Uso**: Leitura rápida, compartilhamento

---

## Artefatos do Run

### Estado da Árvore

**Arquivo**: `runs/70f8222b.json`

**Conteúdo**:
- Estado completo da árvore de busca
- 7 nós serializados
- Fronteira atualizada
- Objetivo completo

### Resultados por Nó

- `experiments/05b55df7/results.json` - Nó raiz (PRELIM)
- `experiments/b1d3809b/results.json` - Nó TUNING 1
- `experiments/ddfebd32/results.json` - Nó TUNING 2

---

## Métricas Principais

| Métrica | Valor |
|---------|-------|
| **Status** | ✅ SUCESSO |
| **Duração** | 0.76s |
| **Nós Criados** | 6 |
| **Nós Executados** | 3 |
| **Erros** | 0 |
| **Taxa de Expansão** | 2.0 |

---

## Comandos Úteis

### Visualizar Relatório Executivo

```bash
cat reports/RELATORIO_EXECUTIVO_TESTE_AO_VIVO.md
```

### Inspecionar Run

```bash
python -m src.cli inspect 70f8222b --out-dir runs --limit 10
```

### Gerar Relatório do Run

```bash
python -m src.cli report 70f8222b --out-dir runs
```

### Analisar JSON

```bash
cat reports/live_test_70f8222b_20251108_175928.json | jq .
```

---

**Última atualização**: 2025-11-08

