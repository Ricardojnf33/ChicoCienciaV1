#!/usr/bin/env python3
"""
Script de teste ao vivo REAL com interações entre agentes CrewAI.

Executa o sistema com agentes LLM reais e captura todas as interações.
"""
import sys
import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import structlog

# Adiciona raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings


class RealLiveTestRunner:
    """Runner para teste ao vivo REAL com agentes CrewAI."""
    
    def __init__(self, objective: str = "objective.live.yaml", budget: int = 2):
        self.objective = objective
        self.budget = budget
        self.start_time = None
        self.end_time = None
        self.run_id = None
        self.metrics: Dict[str, Any] = {
            "test_start": None,
            "test_end": None,
            "duration_seconds": None,
            "run_id": None,
            "objective": objective,
            "budget": budget,
            "mode": "REAL",
            "agent_interactions": [],
            "api_calls": {
                "openai": 0,
                "semantic_scholar": 0,
                "cache_hits": 0,
            },
            "rate_limiting": {
                "waits": 0,
                "total_wait_time": 0.0,
            },
            "nodes_created": 0,
            "nodes_executed": 0,
            "errors": [],
            "warnings": [],
        }
        self.logs: List[Dict[str, Any]] = []
        
    def setup_logging(self):
        """Configura logging estruturado."""
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(10),  # DEBUG
        )
    
    def capture_log_line(self, line: str):
        """Captura e processa linha de log."""
        try:
            log_entry = json.loads(line.strip())
            self.logs.append(log_entry)
            
            # Extrai métricas relevantes
            event = log_entry.get("event", "")
            
            # Captura interações de agentes
            if "crew" in event.lower() or "agent" in event.lower() or "task" in event.lower():
                self.metrics["agent_interactions"].append(log_entry)
            
            if "semantic_scholar" in event:
                if "rate_limit.wait" in event:
                    self.metrics["rate_limiting"]["waits"] += 1
                    self.metrics["rate_limiting"]["total_wait_time"] += log_entry.get("sleep_time", 0)
                elif "search.success" in event:
                    self.metrics["api_calls"]["semantic_scholar"] += 1
            
            if "literature.cache.hit" in event:
                self.metrics["api_calls"]["cache_hits"] += 1
            
            if "ats.iter.start" in event:
                self.metrics["nodes_executed"] += 1
            
            if "ats.iter.children" in event:
                children = log_entry.get("children", [])
                self.metrics["nodes_created"] += len(children)
            
            if log_entry.get("level") == "error":
                self.metrics["errors"].append(log_entry)
            
            if log_entry.get("level") == "warning":
                self.metrics["warnings"].append(log_entry)
                
        except json.JSONDecodeError:
            # Linha não é JSON, pode ser output do CrewAI
            if line.strip():
                self.logs.append({"raw": line.strip(), "timestamp": datetime.utcnow().isoformat()})
    
    def run(self) -> bool:
        """Executa teste ao vivo REAL."""
        print("="*70)
        print("TESTE AO VIVO REAL - ChicoCienciaV1 com CrewAI")
        print("="*70)
        
        settings = Settings()
        
        print(f"\n📋 Configuração:")
        print(f"  Objetivo: {self.objective}")
        print(f"  Budget: {self.budget}")
        print(f"  OpenAI API Key: {'✅ Configurada' if settings.OPENAI_API_KEY else '❌ Não configurada'}")
        print(f"  Semantic Scholar API Key: {'✅ Configurada' if settings.SEMANTIC_SCHOLAR_API_KEY else '❌ Não configurada'}")
        
        if not settings.OPENAI_API_KEY:
            print("\n❌ ERRO: OpenAI API Key não configurada. Teste real requer API key.")
            return False
        
        # Verifica CrewAI
        try:
            from crewai import Agent, Crew, Task
            print(f"  CrewAI: ✅ Instalado")
        except ImportError as e:
            print(f"  CrewAI: ❌ Não instalado: {e}")
            return False
        except Exception as e:
            # Pode ter warnings mas ainda funcionar
            print(f"  CrewAI: ⚠️  Instalado (com warnings)")
        
        self.setup_logging()
        self.start_time = time.time()
        self.metrics["test_start"] = datetime.utcnow().isoformat()
        
        print(f"\n🚀 Iniciando execução REAL com agentes CrewAI...")
        print("-"*70)
        print("⚠️  Esta execução usará créditos de API OpenAI")
        print("-"*70)
        
        # Executa CLI e captura logs
        cmd = [
            sys.executable,
            "-m", "src.cli",
            "init",
            self.objective,
            "--budget", str(self.budget),
            "--out-dir", "runs"
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=project_root
            )
            
            # Captura logs em tempo real
            for line in process.stdout:
                print(line, end="")
                self.capture_log_line(line)
            
            process.wait()
            
            if process.returncode != 0:
                print(f"\n❌ Erro na execução: código {process.returncode}")
                return False
            
            # Extrai run_id dos logs
            for log in self.logs:
                if isinstance(log, dict) and log.get("event") == "init.start":
                    self.run_id = log.get("run_id")
                    self.metrics["run_id"] = self.run_id
                    break
            
            self.end_time = time.time()
            self.metrics["test_end"] = datetime.utcnow().isoformat()
            self.metrics["duration_seconds"] = self.end_time - self.start_time
            
            print("\n" + "-"*70)
            print("✅ Execução REAL concluída!")
            print(f"   Run ID: {self.run_id}")
            print(f"   Duração: {self.metrics['duration_seconds']:.2f}s")
            print(f"   Interações de agentes: {len(self.metrics['agent_interactions'])}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro ao executar: {str(e)}")
            self.metrics["errors"].append({"error": str(e), "type": type(e).__name__})
            import traceback
            traceback.print_exc()
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Gera relatório executivo completo."""
        report = {
            "executive_summary": {
                "test_date": self.metrics["test_start"],
                "run_id": self.metrics["run_id"],
                "status": "SUCCESS" if self.metrics["errors"] == [] else "PARTIAL",
                "duration_seconds": self.metrics["duration_seconds"],
                "objective": self.metrics["objective"],
                "budget": self.metrics["budget"],
                "mode": "REAL",
            },
            "metrics": self.metrics,
            "agent_interactions": {
                "total": len(self.metrics["agent_interactions"]),
                "interactions": self.metrics["agent_interactions"][:50],  # Limita a 50
            },
            "performance": {
                "nodes_per_second": self.metrics["nodes_executed"] / max(self.metrics["duration_seconds"], 1),
                "avg_rate_limit_wait": (
                    self.metrics["rate_limiting"]["total_wait_time"] / 
                    max(self.metrics["rate_limiting"]["waits"], 1)
                ) if self.metrics["rate_limiting"]["waits"] > 0 else 0,
                "cache_hit_rate": (
                    self.metrics["api_calls"]["cache_hits"] / 
                    max(self.metrics["api_calls"]["semantic_scholar"] + self.metrics["api_calls"]["cache_hits"], 1)
                ),
            },
            "api_usage": self.metrics["api_calls"],
            "tree_statistics": {
                "nodes_created": self.metrics["nodes_created"],
                "nodes_executed": self.metrics["nodes_executed"],
                "expansion_rate": self.metrics["nodes_created"] / max(self.metrics["nodes_executed"], 1),
            },
            "errors": self.metrics["errors"],
            "warnings": self.metrics["warnings"],
            "logs_sample": self.logs[-30:] if len(self.logs) > 30 else self.logs,
        }
        
        return report
    
    def save_report(self, output_dir: str = "reports"):
        """Salva relatório em arquivos."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = self.metrics.get("run_id", "unknown")
        
        # JSON completo
        json_path = output_path / f"real_live_test_{run_id}_{timestamp}.json"
        report = self.generate_report()
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        
        # Markdown executivo
        md_path = output_path / f"real_live_test_{run_id}_{timestamp}.md"
        md_content = self.generate_markdown_report(report)
        md_path.write_text(md_content)
        
        print(f"\n📄 Relatórios salvos:")
        print(f"   JSON: {json_path}")
        print(f"   Markdown: {md_path}")
        
        return json_path, md_path
    
    def generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Gera relatório em Markdown."""
        exec_summary = report["executive_summary"]
        perf = report["performance"]
        api = report["api_usage"]
        tree = report["tree_statistics"]
        interactions = report["agent_interactions"]
        
        lines = []
        lines.append("# Relatório Executivo - Teste Ao Vivo REAL")
        lines.append("")
        lines.append(f"**Data**: {exec_summary['test_date']}")
        lines.append(f"**Run ID**: `{exec_summary['run_id']}`")
        lines.append(f"**Status**: {exec_summary['status']}")
        lines.append(f"**Modo**: {exec_summary['mode']}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Sumário Executivo")
        lines.append("")
        lines.append(f"- **Objetivo**: {exec_summary['objective']}")
        lines.append(f"- **Budget**: {exec_summary['budget']} iterações")
        lines.append(f"- **Duração**: {exec_summary['duration_seconds']:.2f} segundos")
        lines.append(f"- **Status**: {'✅ Sucesso' if exec_summary['status'] == 'SUCCESS' else '⚠️ Parcial'}")
        lines.append(f"- **Modo**: REAL (agentes CrewAI executando)")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Interações entre Agentes")
        lines.append("")
        lines.append(f"- **Total de interações capturadas**: {interactions['total']}")
        lines.append("")
        if interactions['interactions']:
            lines.append("### Principais Interações")
            lines.append("")
            for i, interaction in enumerate(interactions['interactions'][:10], 1):
                event = interaction.get("event", "unknown")
                lines.append(f"{i}. **{event}**")
                if "node_id" in interaction:
                    lines.append(f"   - Nó: `{interaction['node_id']}`")
                if "stage" in interaction:
                    lines.append(f"   - Estágio: {interaction['stage']}")
                lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Métricas de Performance")
        lines.append("")
        lines.append(f"- **Nós por segundo**: {perf['nodes_per_second']:.2f}")
        lines.append(f"- **Taxa de cache hit**: {perf['cache_hit_rate']*100:.1f}%")
        lines.append(f"- **Tempo médio de espera (rate limit)**: {perf['avg_rate_limit_wait']:.3f}s")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Uso de API")
        lines.append("")
        lines.append(f"- **Chamadas Semantic Scholar**: {api['semantic_scholar']}")
        lines.append(f"- **Cache hits**: {api['cache_hits']}")
        lines.append(f"- **Rate limit waits**: {api.get('rate_limit_waits', 0)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Estatísticas da Árvore")
        lines.append("")
        lines.append(f"- **Nós criados**: {tree['nodes_created']}")
        lines.append(f"- **Nós executados**: {tree['nodes_executed']}")
        lines.append(f"- **Taxa de expansão**: {tree['expansion_rate']:.2f}")
        lines.append("")
        
        if report["errors"]:
            lines.append("---")
            lines.append("")
            lines.append("## Erros")
            lines.append("")
            for error in report["errors"]:
                lines.append(f"- **{error.get('error_type', 'Unknown')}**: {error.get('error', str(error))}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("## Conclusão")
        lines.append("")
        if exec_summary['status'] == 'SUCCESS':
            lines.append("✅ Teste REAL executado com sucesso. Agentes CrewAI interagiram corretamente.")
        else:
            lines.append("⚠️ Teste executado com alguns problemas. Verificar seção de erros.")
        lines.append("")
        lines.append(f"**Relatório gerado em**: {datetime.now().isoformat()}")
        
        return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Executa teste ao vivo REAL com CrewAI")
    parser.add_argument("--objective", "-o", default="objective.live.yaml", help="Arquivo objetivo YAML")
    parser.add_argument("--budget", "-b", type=int, default=2, help="Budget de iterações")
    parser.add_argument("--output", "-out", default="reports", help="Diretório de saída")
    args = parser.parse_args()
    
    runner = RealLiveTestRunner(objective=args.objective, budget=args.budget)
    
    success = runner.run()
    
    if success:
        runner.save_report(output_dir=args.output)
        print("\n" + "="*70)
        print("✅ TESTE AO VIVO REAL CONCLUÍDO")
        print("="*70)
        return 0
    else:
        print("\n" + "="*70)
        print("❌ TESTE AO VIVO REAL FALHOU")
        print("="*70)
        return 1


if __name__ == "__main__":
    exit(main())

