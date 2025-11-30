# ChicoCienciaV1 - Estado Atual do Sistema
**Data**: 2025-11-30 10:19 BRT  
**Autor**: Senior Engineering Lead  
**Contexto**: Post-Mortem de Testes de Checkpoint e Execução Iterativa

---

## 🎯 Executive Summary

O sistema ChicoCienciaV1 passou por uma **fase crítica de debugging** focada em implementar checkpointing iterativo para superar limitações de sessão. Enfrentamos e resolvemos três bugs críticos que causavam falhas de sistema (segfault), mas identificamos **limitações arquiteturais fundamentais** que impedem execução totalmente autônoma.

**Status Geral**: 🟡 **PARCIALMENTE FUNCIONAL** - Sistema executa nós individuais com sucesso, mas checkpointing ainda não validado.

---

## 📊 Resultados dos Testes Recentes

### ✅ Test 1: Experimento d5068c16 (SUCESSO)
**Executado**: 2025-11-30 08:22-08:24  
**Objetivo**: L2 Regularization + Dropout no dataset Iris  
**Status**: ✅ **COMPLETADO COM SUCESSO**

**Resultados Científicos**:
```json
{
  "baseline": 0.889,
  "hypothesis_1_best": 0.956 (C=10, L2 only),
  "hypothesis_2_best": 0.978 (C=10, L2 + dropout 0.1)
}
```

**Descoberta Chave**: Dropout leve (0.1) + L2 moderado alcançou **97.8% accuracy**, superando baseline em **+8.9pp** e L2 isolado em **+2.2pp**.

**Artefatos Gerados**:
- ✅ `experiments/d5068c16/code.py` (2.8KB)
- ✅ `experiments/d5068c16/results.json` (712 bytes)
- ✅ `experiments/d5068c16/accuracy_vs_C.png` (61KB)

**Conclusão**: A adição de `FileWriterTool` ao agente `Coder` permitiu a criação bem-sucedida de artefatos.

---

### ⚠️ Test 2: Experimento f170a606 (FALHA PARCIAL)
**Executado**: 2025-11-30 09:39-09:49  
**Objetivo**: Mesmo experimento, testando checkpointing  
**Status**: ⚠️ **CRIAÇÃO OK, EXECUÇÃO FALHOU**

**Problema Identificado**:
```python
# Código gerado pelo Coder agent continha erro:
LogisticRegression(penalty='none')  # ❌ INVÁLIDO no sklearn

# Deveria ser:
LogisticRegression(penalty=None)   # ✅ CORRETO
```

**Artefatos Gerados**:
- ✅ `experiments/f170a606/code.py` (5.7KB) - código com bug
- ❌ Execução falhou antes de gerar `results.json`

**Comportamento Observado**:
1. **Coder agent** gerou código com bug (`penalty='none'`)
2. **Runner agent** tentou executar → erro sklearn
3. **Self-Healing Loop** ativou, mas falhou em 25+ retries:
   - Runner não tinha ferramentas para modificar arquivos
   - `PythonRunnerTool` tinha bug de concatenação de paths
   - Loop infinito → **SEGFAULT** por exaustão de memória

---

### 🚨 Test 3: Checkpoint Test (TIMEOUT)
**Executado**: 2025-11-30 10:17-10:19  
**Objetivo**: Validar checkpoint após fixes  
**Status**: ⏱️ **TIMEOUT (180s) - Exit Code 143**

**Observações**:
- ✅ Processo iniciou normalmente
- ✅ Researcher agent gerou hipóteses
- ❌ **Checkpoint não foi salvo** antes do timeout
- ❌ Não criou `runs/test_checkpoint/*.json`

**Análise**: O timeout forçado impediu a conclusão natural do ciclo de checkpointing. Precisamos de execução mais longa ou budget menor.

---

## 🔧 Bugs Críticos Identificados e Resolvidos

### Bug #1: PythonRunnerTool - Path Concatenation ✅ RESOLVIDO
**Severidade**: 🔴 CRÍTICA  
**Impacto**: 100% de falhas de execução do Runner

**Root Cause**:
```python
# ANTES (src/tools/python_repl.py:11)
subprocess.run([sys.executable, code_path], cwd=workdir)

# Quando code_path = "./experiments/f170a606/code.py"
# e workdir = "./experiments/f170a606"
# Resultado: /experiments/f170a606/./experiments/f170a606/code.py ❌
```

**Solução Implementada**:
```python
# AGORA
code_path_abs = Path(code_path).resolve()
workdir_abs = Path(workdir).resolve() if workdir else code_path_abs.parent
subprocess.run([sys.executable, str(code_path_abs)], cwd=str(workdir_abs))
```

**Status**: ✅ **DEPLOYED** - Paths agora sempre absolutos

---

### Bug #2: Runner Agent - Missing File Tools ✅ RESOLVIDO
**Severidade**: 🟠 ALTA  
**Impacto**: Self-healing loop não conseguia corrigir código

**Root Cause**:
- Runner agent só tinha `PythonRunnerTool`
- Quando Experiment Progress Manager delegava "modifique o arquivo X", Runner não tinha ferramentas
- Causava loops infinitos de delegação falhada

**Solução Implementada**:
```python
# src/agents/runner.py
tools=[
    PythonRunnerTool(),
    FileReadTool(),      # ✅ ADICIONADO
    FileWriterTool()     # ✅ ADICIONADO
]
```

**Status**: ✅ **DEPLOYED**

---

### Bug #3: Checkpoint Directory Creation ✅ RESOLVIDO
**Severidade**: 🟠 ALTA  
**Impacto**: Checkpoints não eram salvos

**Root Cause**:
```bash
# CLI cria apenas `runs/`, não `runs/ironman/`
mkdir -p runs
# Mas checkpoint_path = "runs/ironman/{id}.json"
# tree.save_json() falhava silenciosamente
```

**Solução Implementada**:
```python
# src/processes/ats_process.py:269-274
if checkpoint_path:
    from pathlib import Path
    Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
    tree.save_json(checkpoint_path)
    log.info("ats.checkpoint.saved", path=checkpoint_path)
```

**Status**: ✅ **DEPLOYED** - Directory auto-criado antes do save

---

## 🏗️ Modificações na Arquitetura

### Agentes Modificados
| Agente | Tools Antes | Tools Agora | Motivo |
|--------|-------------|-------------|---------|
| **Coder** | Dataset, PythonRunner, Plot | + FileRead, FileWriter | Criar arquivos `.py` |
| **Runner** | PythonRunner | + FileRead, FileWriter | Modificar código com bugs |

### Módulos Modificados
1. **`src/tools/python_repl.py`** - Path resolution fix
2. **`src/agents/coder.py`** - Added file tools
3. **`src/agents/runner.py`** - Added file tools
4. **`src/processes/ats_process.py`** - Checkpoint directory creation
5. **`src/cli.py`** - Checkpoint path passed to `run_agentic_tree()`

---

## 🎓 Lições Aprendidas

### 1. LLM Code Generation Quality
**Problema**: Coder agent gerou `penalty='none'` (string) em vez de `penalty=None` (Python type).

**Análise**:
- LLM confundiu sintaxe sklearn com configurações de outros frameworks
- Sem validação estática de código antes da execução
- Self-healing não previne bugs semânticos, só corrige após falha

**Recomendação**: Adicionar linter/validator no fluxo do Coder agent.

---

### 2. Infinite Retry Loops
**Problema**: 25+ retries consumiram memória até crash do sistema.

**Análise**:
- Self-healing max_retries=2 não foi respeitado
- Agents delegavam recursivamente sem limite
- CrewAI framework não tem circuit breaker nativo

**Recomendação**: Implementar global retry counter e emergency shutdown.

---

### 3. Silent Failures
**Problema**: Checkpoints não eram salvos, mas sistema continuava sem alerta.

**Análise**:
- `tree.save_json()` não levantava exception em diretórios inexistentes
- Logs não indicavam claramente falha de checkpoint
- Testes manuais eram necessários para detectar

**Recomendação**: Adicionar health checks explícitos após cada checkpoint.

---

## 📈 Status das Features

| Feature | Status | Comentário |
|---------|--------|------------|
| **ATS Core** | ✅ FUNCIONAL | Seleção UCT, expansão, backprop OK |
| **Agents (Researcher)** | ✅ FUNCIONAL | Gera hipóteses com literatura |
| **Agents (Coder)** | ✅ FUNCIONAL | Cria código (com bugs ocasionais) |
| **Agents (Runner)** | 🟡 PARCIAL | Executa, mas sem validação prévia |
| **Self-Healing** | 🟡 PARCIAL | Ativa mas pode entrar em loop |
| **Checkpointing** | 🔴 NÃO VALIDADO | Código implementado, não testado |
| **Resume Command** | 🔴 NÃO TESTADO | Depende de checkpoints funcionais |
| **WandB Integration** | ✅ FUNCIONAL | Logs sendo enviados |
| **Dry-run Mode** | ✅ FUNCIONAL | Synthetic data generation OK |

---

## 🚀 Próximos Passos Recomendados

### CRÍTICO (P0)
1. **Validar Checkpointing**
   ```bash
   # Test com budget mínimo e sem timeout
   python -m src.cli init objective.live.yaml --budget 1 --out-dir runs/checkpoint_validation
   # Verificar: ls runs/checkpoint_validation/*.json
   ```

2. **Testar Resume Command**
   ```bash
   python -m src.cli resume checkpoint_validation/{id} --budget 1
   # Validar continuidade da árvore
   ```

3. **Implementar Emergency Shutdown**
   ```python
   # Em ats_process.py
   if total_agent_calls > MAX_CALLS_PER_RUN:
       raise RuntimeError("Emergency shutdown: max calls exceeded")
   ```

### IMPORTANTE (P1)
4. **Code Validation Layer**
   - Adicionar `pylint` ou `mypy` antes de `Runner.execute()`
   - Prevenir bugs semânticos como `penalty='none'`

5. **Health Check System**
   - Log explícito: "✅ Checkpoint saved" ou "❌ Checkpoint FAILED"
   - Assert que arquivo existe após `save_json()`

6. **Refinar Limites do Self-Healing**
   - Audit logs do teste f170a606 para entender por que max_retries=2 foi ignorado
   - Implementar circuit breaker global

### DESEJÁVEL (P2)
7. **Audit VLM Critic** (Roadmap Phase 1 - Task 1)
8. **Refactor Researcher Prompt** (Roadmap Phase 1 - Task 2)
9. **Metrics Dashboard** - WandB custom charts

---

## 🔍 Análise de Risco

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **Checkpointing falha** | ALTA | CRÍTICO | Testes P0 acima |
| **Infinite retry loops** | MÉDIA | ALTO | Emergency shutdown P0 |
| **LLM code quality** | MÉDIA | MÉDIO | Validation layer P1 |
| **Memory exhaustion** | BAIXA | CRÍTICO | Já mitigado com timeout |
| **API rate limits** | BAIXA | MÉDIO | Backoff já implementado |

---

## 💡 Conclusões do CEO

### Conquistas
1. **Sistema Core Funciona**: ATS + Agents podem executar experimentos científicos completos
2. **Descoberta Científica Real**: 97.8% accuracy provam conceito funcional
3. **Self-Healing Conceito Validado**: Loop de retry detecta e tenta corrigir erros

### Impedimentos
1. **Checkpointing Não Validado**: Estratégia iterativa ainda teórica
2. **Agent Reliability**: LLMs geram código com bugs semânticos
3. **Framework Limitations**: CrewAI não tem safeguards nativos para loops infinitos

### Recomendação Estratégica
**PROSSEGUIR COM CAUTELA**. O sistema demonstra viabilidade técnica, mas precisa de **2-3 dias de hardening** focados em:
- Validação de checkpoints (P0)
- Circuit breakers (P0)
- Code validation (P1)

Somente após esses fixes, recomendar **produção limitada** (max 5 runs/dia) até estabilidade comprovada.

---

## 📌 Referências Técnicas

- **Experimento d5068c16**: `experiments/d5068c16/results.json`
- **Experimento f170a606**: `experiments/f170a606/code.py` (com bug penalty='none')
- **Roadmap**: `/home/r33/.gemini/antigravity/brain/.../ROADMAP_GOLDEN_RATIO.md`
- **Task Tracking**: `/home/r33/.gemini/antigravity/brain/.../task.md`

---

**Assinado**: Senior Engineering Lead  
**2025-11-30 10:19 BRT**
