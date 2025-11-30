"""
Adaptadores para tornar tools customizadas compatíveis com CrewAI.

CrewAI requer tools que herdem de BaseTool ou sejam funções específicas.
Este módulo cria wrappers compatíveis.
"""
try:
    from crewai.tools.base_tool import BaseTool
    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    try:
        from crewai_tools import BaseTool
        CREWAI_TOOLS_AVAILABLE = True
    except ImportError:
        CREWAI_TOOLS_AVAILABLE = False
        BaseTool = None

from typing import Any, Dict, List
from src.tools.literature import LiteratureTool as BaseLiteratureTool
from src.tools.datasets import DatasetTool as BaseDatasetTool
from src.tools.python_repl import PythonRunnerTool as BasePythonRunnerTool
from src.tools.plotting import PlotTool as BasePlotTool
from src.tools.metrics import MetricsTool as BaseMetricsTool


if CREWAI_TOOLS_AVAILABLE and BaseTool:
    class LiteratureTool(BaseTool):
        """Wrapper CrewAI para LiteratureTool."""
        name: str = "literature_search"
        description: str = "Busca papers científicos no Semantic Scholar e ArXiv"
        
        def __init__(self):
            super().__init__()
            self._tool = BaseLiteratureTool()
        
        def _run(self, query: str, k: int = 5) -> str:
            """Executa busca de literatura."""
            results = self._tool.search(query, k=k)
            return self._tool.summarize(results)
    
    class DatasetTool(BaseTool):
        """Wrapper CrewAI para DatasetTool."""
        name: str = "dataset_loader"
        description: str = "Carrega datasets (ex: iris) com split treino/teste"
        
        def __init__(self):
            super().__init__()
            self._tool = BaseDatasetTool()
        
        def _run(self, name: str = "iris", test_size: float = 0.25, seed: int = 42) -> str:
            """Carrega dataset."""
            dataset = self._tool.load(name, test_size, seed)
            return f"Dataset {dataset.name} carregado: {len(dataset.X_train)} treino, {len(dataset.X_test)} teste"
    
    class PythonRunnerTool(BaseTool):
        """Wrapper CrewAI para PythonRunnerTool."""
        name: str = "python_executor"
        description: str = "Executa scripts Python em sandbox e captura output"
        
        def __init__(self):
            super().__init__()
            self._tool = BasePythonRunnerTool()
        
        def _run(self, code_path: str, workdir: str = None, timeout: int = 180) -> str:
            """Executa script Python."""
            result = self._tool.run_script(code_path, workdir, timeout)
            if result["returncode"] == 0:
                return f"✅ Execução bem-sucedida:\n{result['stdout']}"
            else:
                return f"❌ Erro (código {result['returncode']}):\n{result['stderr']}"
    
    class PlotTool(BaseTool):
        """Wrapper CrewAI para PlotTool."""
        name: str = "plot_generator"
        description: str = "Gera figuras (lineplots, etc) e salva como PNG"
        
        def __init__(self):
            super().__init__()
            self._tool = BasePlotTool()
        
        def _run(self, xs: List[float], ys: List[float], title: str, out_path: str) -> str:
            """Gera plot."""
            meta = self._tool.save_lineplot(xs, ys, title, out_path)
            if meta.get("generated"):
                return f"✅ Figura gerada: {out_path}"
            else:
                return f"⚠️ Figura não gerada (matplotlib não disponível): {out_path}"
    
    class MetricsTool(BaseTool):
        """Wrapper CrewAI para MetricsTool."""
        name: str = "metrics_evaluator"
        description: str = "Treina modelo e avalia métricas (accuracy, etc)"
        
        def __init__(self):
            super().__init__()
            self._tool = BaseMetricsTool()
        
        def _run(self, dataset, l2: float = 1.0, max_iter: int = 200, out_path: str = "./results.json") -> str:
            """Treina e avalia."""
            result = self._tool.train_eval_logreg(dataset, l2, max_iter, out_path)
            return f"✅ Métricas: accuracy={result['accuracy']:.4f}, salvo em {result['results_path']}"

else:
    # Fallback: retorna as classes originais se crewai_tools não disponível
    LiteratureTool = BaseLiteratureTool
    DatasetTool = BaseDatasetTool
    PythonRunnerTool = BasePythonRunnerTool
    PlotTool = BasePlotTool
    MetricsTool = BaseMetricsTool

