import threading
import time
from collections.abc import Callable
from typing import Any

import structlog
from requests.exceptions import HTTPError, RequestException, Timeout
from semanticscholar import SemanticScholar
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class SemanticScholarClient:
    """
    Cliente para Semantic Scholar API com rate limiting e retry automático.
    
    Rate limit: 1 requisição por segundo (cumulativo em todos os endpoints).
    Implementa rate limiting global usando threading.Lock para garantir
    que múltiplas instâncias/threads respeitem o limite.
    """
    # Rate limiting global (class-level)
    _last_request_time: float | None = None
    _lock: threading.Lock = threading.Lock()
    _min_interval: float = 1.1  # 1.1s para margem de segurança (default)

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 20,
        min_interval: float | None = None,
        *,
        client: Any | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        """
        Inicializa cliente Semantic Scholar.
        
        Args:
            api_key: Chave da API (enviada como x-api-key header)
            timeout: Timeout em segundos para requisições
            min_interval: Intervalo mínimo entre requisições em segundos (usa Settings se None)
        """
        from src.config.settings import Settings
        settings = Settings()
        self.client = client or SemanticScholar(api_key=api_key, timeout=timeout)
        self._min_interval = (
            min_interval
            if min_interval is not None
            else settings.SEMANTIC_SCHOLAR_RATE_LIMIT
        )
        if self._min_interval < 0:
            raise ValueError("min_interval não pode ser negativo")
        self._clock = clock
        self._sleeper = sleeper
        self.log = structlog.get_logger()

    def _rate_limit(self):
        """
        Garante intervalo mínimo entre requisições usando lock global.
        
        Thread-safe: múltiplas instâncias/threads compartilham o mesmo lock,
        garantindo que apenas 1 requisição ocorra por segundo.
        """
        limiter = type(self)
        with limiter._lock:
            now = self._clock()
            if limiter._last_request_time is None:
                limiter._last_request_time = now
                return
            elapsed = now - limiter._last_request_time
            if elapsed < self._min_interval:
                sleep_time = self._min_interval - elapsed
                self.log.debug(
                    "semantic_scholar.rate_limit.wait",
                    sleep_time=sleep_time,
                    elapsed=elapsed
                )
                self._sleeper(sleep_time)
            limiter._last_request_time = self._clock()

    @classmethod
    def _reset_rate_limit_for_tests(cls) -> None:
        with cls._lock:
            cls._last_request_time = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((HTTPError, Timeout, RequestException)),
        reraise=True
    )
    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
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

        results: list[dict[str, Any]] = []
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
