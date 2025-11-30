#!/usr/bin/env python3
"""
Script de teste ao vivo completo com captura de logs e métricas.

Executa o sistema ChicoCienciaV1 em modo real e gera relatórios executivos.
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


class LiveTestRunner:
    """Runner para teste ao vivo com captura completa de métricas."""
    
    def __init__(self, objective: str = "objective.live.yaml", budget: int = 3):
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
            "api_calls": {
                "semantic_scholar": 0,
                "arxiv": 0,
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
            # Linha não é JSON, ignora
            pass
    
    def run(self) -> bool:
        """Executa teste ao vivo."""
        print("="*70)
        print("TESTE AO VIVO - ChicoCienciaV1")
        print("="*70)
        
        settings = Settings()
        
        print(f"\n📋 Configuração:")
        print(f"  Objetivo: {self.objective}")
        print(f"  Budget: {self.budget}")
        print(f"  OpenAI API Key: {'✅ Configurada' if settings.OPENAI_API_KEY else '❌ Não configurada'}")
        print(f"  Semantic Scholar API Key: {'✅ Configurada' if settings.SEMANTIC_SCHOLAR_API_KEY else '❌ Não configurada'}")
        print(f"  Rate Limit: {settings.SEMANTIC_SCHOLAR_RATE_LIMIT}s")
        print(f"  Cache TTL: {settings.SEMANTIC_SCHOLAR_CACHE_TTL}s")
        
        if not settings.OPENAI_API_KEY:
            print("\n⚠️  AVISO: OpenAI API Key não configurada. Executando em modo dry-run.")
        
        self.setup_logging()
        self.start_time = time.time()
        self.metrics["test_start"] = datetime.utcnow().isoformat()
        
        print(f"\n🚀 Iniciando execução...")
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
                if log.get("event") == "init.start":
                    self.run_id = log.get("run_id")
                    self.metrics["run_id"] = self.run_id
                    break
            
            self.end_time = time.time()
            self.metrics["test_end"] = datetime.utcnow().isoformat()
            self.metrics["duration_seconds"] = self.end_time - self.start_time
            
            print("\n" + "-"*70)
            print("✅ Execução concluída com sucesso!")
            print(f"   Run ID: {self.run_id}")
            print(f"   Duração: {self.metrics['duration_seconds']:.2f}s")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro ao executar: {str(e)}")
            self.metrics["errors"].append({"error": str(e), "type": type(e).__name__})
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
            },
            "metrics": self.metrics,
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
            "api_usage": {
                "semantic_scholar_calls": self.metrics["api_calls"]["semantic_scholar"],
                "cache_hits": self.metrics["api_calls"]["cache_hits"],
                "rate_limit_waits": self.metrics["rate_limiting"]["waits"],
                "total_wait_time": self.metrics["rate_limiting"]["total_wait_time"],
            },
            "tree_statistics": {
                "nodes_created": self.metrics["nodes_created"],
                "nodes_executed": self.metrics["nodes_executed"],
                "expansion_rate": self.metrics["nodes_created"] / max(self.metrics["nodes_executed"], 1),
            },
            "errors": self.metrics["errors"],
            "warnings": self.metrics["warnings"],
            "logs_sample": self.logs[-20:] if len(self.logs) > 20 else self.logs,
        }
        
        return report
    
    def save_report(self, output_dir: str = "reports"):
        """Salva relatório em arquivos."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = self.metrics.get("run_id", "unknown")
        
        # JSON completo
        json_path = output_path / f"live_test_{run_id}_{timestamp}.json"
        report = self.generate_report()
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        
        # Markdown executivo
        md_path = output_path / f"live_test_{run_id}_{timestamp}.md"
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
        
        lines = []
        lines.append("# Relatório Executivo - Teste Ao Vivo")
        lines.append("")
        lines.append(f"**Data**: {exec_summary['test_date']}")
        lines.append(f"**Run ID**: `{exec_summary['run_id']}`")
        lines.append(f"**Status**: {exec_summary['status']}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Sumário Executivo")
        lines.append("")
        lines.append(f"- **Objetivo**: {exec_summary['objective']}")
        lines.append(f"- **Budget**: {exec_summary['budget']} iterações")
        lines.append(f"- **Duração**: {exec_summary['duration_seconds']:.2f} segundos")
        lines.append(f"- **Status**: {'✅ Sucesso' if exec_summary['status'] == 'SUCCESS' else '⚠️ Parcial'}")
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
        lines.append(f"- **Chamadas Semantic Scholar**: {api['semantic_scholar_calls']}")
        lines.append(f"- **Cache hits**: {api['cache_hits']}")
        lines.append(f"- **Rate limit waits**: {api['rate_limit_waits']}")
        lines.append(f"- **Tempo total de espera**: {api['total_wait_time']:.2f}s")
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
        
        if report["warnings"]:
            lines.append("---")
            lines.append("")
            lines.append("## Avisos")
            lines.append("")
            for warning in report["warnings"][:10]:  # Limita a 10
                lines.append(f"- {warning.get('event', 'Unknown')}: {warning.get('error', str(warning))}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("## Conclusão")
        lines.append("")
        if exec_summary['status'] == 'SUCCESS':
            lines.append("✅ Teste executado com sucesso. Sistema operando conforme esperado.")
        else:
            lines.append("⚠️ Teste executado com alguns problemas. Verificar seção de erros.")
        lines.append("")
        lines.append(f"**Relatório gerado em**: {datetime.now().isoformat()}")
        
        return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Executa teste ao vivo completo")
    parser.add_argument("--objective", "-o", default="objective.live.yaml", help="Arquivo objetivo YAML")
    parser.add_argument("--budget", "-b", type=int, default=3, help="Budget de iterações")
    parser.add_argument("--output", "-out", default="reports", help="Diretório de saída")
    args = parser.parse_args()
    
    runner = LiveTestRunner(objective=args.objective, budget=args.budget)
    
    success = runner.run()
    
    if success:
        runner.save_report(output_dir=args.output)
        print("\n" + "="*70)
        print("✅ TESTE AO VIVO CONCLUÍDO")
        print("="*70)
        return 0
    else:
        print("\n" + "="*70)
        print("❌ TESTE AO VIVO FALHOU")
        print("="*70)
        return 1


if __name__ == "__main__":
    exit(main())

