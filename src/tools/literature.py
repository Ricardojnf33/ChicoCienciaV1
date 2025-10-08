from typing import List, Dict, Any
from dataclasses import dataclass
from src.config.settings import Settings

try:
    from src.clients.arxiv_client import ArxivClient
    from src.clients.semantic_scholar_client import SemanticScholarClient
except Exception:  # fallback para evitar crash em ambientes sem deps
    ArxivClient = None  # type: ignore
    SemanticScholarClient = None  # type: ignore


@dataclass
class LiteratureTool:
    name: str = "literature_tool"

    def __post_init__(self):
        settings = Settings()
        self._arxiv = ArxivClient(max_results=5) if ArxivClient else None
        self._s2 = (
            SemanticScholarClient(api_key=settings.SEMANTIC_SCHOLAR_API_KEY)
            if SemanticScholarClient
            else None
        )

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        # Tenta Semantic Scholar
        if self._s2:
            try:
                results.extend(self._s2.search(query, limit=k))
            except Exception:
                pass
        # Tenta ArXiv
        if self._arxiv and len(results) < k:
            try:
                results.extend(self._arxiv.search(query)[: max(0, k - len(results))])
            except Exception:
                pass
        # Fallback se vazio
        if not results:
            results = [
                {"title": f"Paper about {query} (mock)", "year": 2024, "url": "https://example.org"},
                {"title": f"Another {query} study (mock)", "year": 2023, "url": "https://example.org"},
            ][:k]
        return results

    def summarize(self, items: List[Dict[str, Any]]) -> str:
        bullets = [f"- {it.get('title')} ({it.get('year')})" for it in items]
        return "\n".join(bullets)
