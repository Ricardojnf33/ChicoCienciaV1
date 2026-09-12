"""Adaptadores das ferramentas locais para o contrato LangChain usado pelo CrewAI 0.51."""

from typing import Any

from langchain_core.tools import BaseTool
from pydantic.v1 import PrivateAttr

from src.tools.datasets import DatasetTool as BaseDatasetTool
from src.tools.literature import LiteratureTool as BaseLiteratureTool
from src.tools.metrics import MetricsTool as BaseMetricsTool
from src.tools.plotting import PlotTool as BasePlotTool
from src.tools.python_repl import PythonRunnerTool as BasePythonRunnerTool


class LiteratureTool(BaseTool):
    name: str = "literature_search"
    description: str = "Busca papers científicos no Semantic Scholar e ArXiv."
    _tool: BaseLiteratureTool = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._tool = BaseLiteratureTool()

    def _run(self, query: str, k: int = 5) -> str:
        results = self._tool.search(query, k=k)
        return self._tool.summarize(results)


class DatasetTool(BaseTool):
    name: str = "dataset_loader"
    description: str = "Carrega dataset público com split de treino e teste."
    _tool: BaseDatasetTool = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._tool = BaseDatasetTool()

    def _run(self, name: str = "iris", test_size: float = 0.25, seed: int = 42) -> str:
        dataset = self._tool.load(name, test_size, seed)
        return (
            f"Dataset {dataset.name} carregado: {len(dataset.X_train)} treino, "
            f"{len(dataset.X_test)} teste"
        )


class PlotTool(BaseTool):
    name: str = "plot_generator"
    description: str = "Gera uma figura de linha e salva como PNG."
    _tool: BasePlotTool = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._tool = BasePlotTool()

    def _run(self, xs: list[float], ys: list[float], title: str, out_path: str) -> str:
        metadata = self._tool.save_lineplot(xs, ys, title, out_path)
        if metadata.get("generated"):
            return f"Figura gerada: {out_path}"
        return f"Figura não gerada: {out_path}"


class MetricsTool(BaseTool):
    name: str = "metrics_evaluator"
    description: str = "Treina regressão logística e grava métricas."
    _tool: BaseMetricsTool = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._tool = BaseMetricsTool()

    def _run(
        self,
        dataset: Any,
        l2: float = 1.0,
        max_iter: int = 200,
        out_path: str = "./results.json",
    ) -> str:
        result = self._tool.train_eval_logreg(dataset, l2, max_iter, out_path)
        return (
            f"Métricas: accuracy={result['accuracy']:.4f}, "
            f"salvo em {result['results_path']}"
        )


class PythonRunnerTool(BaseTool):
    name: str = "python_executor"
    description: str = "Executa script no runner controlado e captura a evidência."
    _tool: BasePythonRunnerTool = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._tool = BasePythonRunnerTool()

    def _run(
        self,
        code_path: str,
        workdir: str | None = None,
        timeout: int = 180,
    ) -> str:
        result = self._tool.run_script(code_path, workdir, timeout)
        if result["returncode"] == 0:
            return f"Execução bem-sucedida:\n{result['stdout']}"
        return f"Erro (código {result['returncode']}):\n{result['stderr']}"
