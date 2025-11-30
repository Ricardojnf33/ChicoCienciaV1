import time
from typing import List, Dict, Any
from dataclasses import dataclass, field
from src.config.settings import Settings
import structlog

try:
    from src.clients.arxiv_client import ArxivClient
    from src.clients.semantic_scholar_client import SemanticScholarClient
except Exception:  # fallback para evitar crash em ambientes sem deps
    ArxivClient = None  # type: ignore
    SemanticScholarClient = None  # type: ignore


@dataclass
class LiteratureTool:
    """
    Ferramenta de busca de literatura com cache e fallback gracioso.
    
    Implementa cache em memória com TTL configurável para evitar
    requisições duplicadas ao Semantic Scholar.
    """
    name: str = "literature_tool"
    _cache: Dict[str, tuple] = field(default_factory=dict, repr=False)  # (results, timestamp)
    _cache_ttl: int = 3600  # 1 hora (default)

    def __post_init__(self):
        settings = Settings()
        self._arxiv = ArxivClient(max_results=5) if ArxivClient else None
        self._s2 = (
            SemanticScholarClient(api_key=settings.SEMANTIC_SCHOLAR_API_KEY)
            if SemanticScholarClient
            else None
        )
        self._cache_ttl = settings.SEMANTIC_SCHOLAR_CACHE_TTL
        self.log = structlog.get_logger()

    def _get_cached(self, cache_key: str) -> List[Dict[str, Any]] | None:
        """
        Retorna resultado do cache se válido.
        
        Args:
            cache_key: Chave do cache (query:k)
            
        Returns:
            Resultados do cache ou None se expirado/inexistente
        """
        if cache_key in self._cache:
            results, timestamp = self._cache[cache_key]
            elapsed = time.time() - timestamp
            if elapsed < self._cache_ttl:
                self.log.debug(
                    "literature.cache.hit",
                    cache_key=cache_key,
                    age_seconds=elapsed
                )
                return results
            else:
                # Cache expirado, remove
                del self._cache[cache_key]
                self.log.debug(
                    "literature.cache.expired",
                    cache_key=cache_key,
                    age_seconds=elapsed
                )
        return None

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Busca literatura com cache, rate limiting e fallback gracioso.
        
        Ordem de tentativas:
        1. Cache (se válido)
        2. Semantic Scholar (com rate limiting)
        3. ArXiv (fallback)
        4. Mock (último recurso)
        
        Args:
            query: Query de busca
            k: Número máximo de resultados
            
        Returns:
            Lista de dicionários com informações dos papers
        """
        cache_key = f"{query}:{k}"
        
        # Verifica cache primeiro
        cached = self._get_cached(cache_key)
        if cached:
            return cached[:k]
        
        results: List[Dict[str, Any]] = []
        
        # Tenta Semantic Scholar (com rate limiting e retry)
        if self._s2:
            try:
                s2_results = self._s2.search(query, limit=k)
                results.extend(s2_results)
                # Atualiza cache apenas se obteve resultados
                if s2_results:
                    self._cache[cache_key] = (s2_results, time.time())
                    self.log.debug(
                        "literature.s2.success",
                        query=query,
                        results_count=len(s2_results),
                        cached=True
                    )
            except Exception as e:
                self.log.warning(
                    "literature.s2_failed",
                    query=query,
                    error=str(e),
                    error_type=type(e).__name__
                )
        
        # Fallback para ArXiv se não obteve resultados suficientes
        if self._arxiv and len(results) < k:
            try:
                arxiv_results = self._arxiv.search(query)[:max(0, k - len(results))]
                results.extend(arxiv_results)
                self.log.debug(
                    "literature.arxiv.fallback",
                    query=query,
                    results_count=len(arxiv_results)
                )
            except Exception as e:
                self.log.warning(
                    "literature.arxiv_failed",
                    query=query,
                    error=str(e)
                )
        
        # Fallback para mock se ainda vazio
        if not results:
            results = [
                {"title": f"Paper about {query} (mock)", "year": 2024, "url": "https://example.org"},
                {"title": f"Another {query} study (mock)", "year": 2023, "url": "https://example.org"},
            ][:k]
            self.log.debug(
                "literature.mock.fallback",
                query=query,
                results_count=len(results)
            )
        
        return results

    def summarize(self, items: List[Dict[str, Any]]) -> str:
        bullets = [f"- {it.get('title')} ({it.get('year')})" for it in items]
        return "\n".join(bullets)
