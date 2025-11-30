import time
import threading
from typing import List, Dict, Any
from semanticscholar import SemanticScholar
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from requests.exceptions import HTTPError, Timeout, RequestException
import structlog


class SemanticScholarClient:
    """
    Cliente para Semantic Scholar API com rate limiting e retry automático.
    
    Rate limit: 1 requisição por segundo (cumulativo em todos os endpoints).
    Implementa rate limiting global usando threading.Lock para garantir
    que múltiplas instâncias/threads respeitem o limite.
    """
    # Rate limiting global (class-level)
    _last_request_time: float = 0.0
    _lock: threading.Lock = threading.Lock()
    _min_interval: float = 1.1  # 1.1s para margem de segurança (default)

    def __init__(self, api_key: str | None = None, timeout: int = 20, min_interval: float | None = None):
        """
        Inicializa cliente Semantic Scholar.
        
        Args:
            api_key: Chave da API (enviada como x-api-key header)
            timeout: Timeout em segundos para requisições
            min_interval: Intervalo mínimo entre requisições em segundos (usa Settings se None)
        """
        from src.config.settings import Settings
        settings = Settings()
        self.client = SemanticScholar(api_key=api_key, timeout=timeout)
        self._min_interval = min_interval or settings.SEMANTIC_SCHOLAR_RATE_LIMIT
        self.log = structlog.get_logger()

    def _rate_limit(self):
        """
        Garante intervalo mínimo entre requisições usando lock global.
        
        Thread-safe: múltiplas instâncias/threads compartilham o mesmo lock,
        garantindo que apenas 1 requisição ocorra por segundo.
        """
        with self._lock:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_interval:
                sleep_time = self._min_interval - elapsed
                self.log.debug(
                    "semantic_scholar.rate_limit.wait",
                    sleep_time=sleep_time,
                    elapsed=elapsed
                )
                time.sleep(sleep_time)
            self._last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((HTTPError, Timeout, RequestException)),
        reraise=True
    )
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Busca papers no Semantic Scholar com rate limiting e retry automático.
        
        Args:
            query: Query de busca
            limit: Número máximo de resultados
            
        Returns:
            Lista de dicionários com informações dos papers
            
        Raises:
            HTTPError: Se API retornar erro após 3 tentativas
            Timeout: Se requisição exceder timeout após 3 tentativas
        """
        self._rate_limit()  # Aplica rate limiting antes da requisição

        try:
            papers = self.client.search_paper(query=query, limit=limit)
        except (HTTPError, Timeout, RequestException) as e:
            self.log.warning(
                "semantic_scholar.search.error",
                query=query,
                limit=limit,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
        except Exception as e:
            # Erros não relacionados a rede não devem ser retried
            self.log.error(
                "semantic_scholar.search.unexpected_error",
                query=query,
                error=str(e),
                error_type=type(e).__name__
            )
            raise

        results: List[Dict[str, Any]] = []
        for p in papers:
            url = None
            if p.openAccessPdf:
                url = p.openAccessPdf.get("url")
            if not url and p.externalIds:
                # fallback: use S2 url
                url = f"https://www.semanticscholar.org/paper/{p.paperId}"
            results.append({
                "title": p.title,
                "year": p.year,
                "url": url,
                "summary": p.abstract,
                "source": "semantic_scholar",
            })
        
        self.log.debug(
            "semantic_scholar.search.success",
            query=query,
            results_count=len(results)
        )
        return results


