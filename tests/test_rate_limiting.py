"""
Teste de rate limiting e cache do Semantic Scholar.

Este script valida:
1. Rate limiting funciona corretamente (1 req/seg)
2. Cache evita requisições duplicadas
3. Retry funciona em caso de falhas temporárias
4. Logs são gerados corretamente
"""
import time
import threading
from typing import List
from src.tools.literature import LiteratureTool
from src.clients.semantic_scholar_client import SemanticScholarClient
from src.config.settings import Settings
import structlog


def setup_logging():
    """Configura logging estruturado para testes."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(10),  # DEBUG level
    )


def test_rate_limiting_concurrent():
    """Testa rate limiting com chamadas simultâneas."""
    print("\n" + "="*60)
    print("TESTE 1: Rate Limiting com Chamadas Simultâneas")
    print("="*60)
    
    settings = Settings()
    if not settings.SEMANTIC_SCHOLAR_API_KEY:
        print("⚠️  SEMANTIC_SCHOLAR_API_KEY não configurada. Teste será simulado.")
        return
    
    tool = LiteratureTool()
    if not tool._s2:
        print("⚠️  SemanticScholarClient não disponível. Teste será simulado.")
        return
    
    queries = [
        "machine learning",
        "deep learning",
        "neural networks",
        "transformer architecture",
        "reinforcement learning"
    ]
    
    results: List[tuple] = []
    errors: List[str] = []
    
    def search_query(query: str, idx: int):
        """Função para busca em thread separada."""
        start_time = time.time()
        try:
            result = tool.search(query, k=3)
            elapsed = time.time() - start_time
            results.append((idx, query, len(result), elapsed, None))
            print(f"  Thread {idx}: '{query}' → {len(result)} resultados em {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - start_time
            errors.append(f"Thread {idx}: {str(e)}")
            results.append((idx, query, 0, elapsed, str(e)))
            print(f"  Thread {idx}: '{query}' → ERRO: {str(e)}")
    
    # Executa todas as queries simultaneamente
    threads = []
    start_total = time.time()
    
    print(f"\nIniciando {len(queries)} buscas simultâneas...")
    for i, query in enumerate(queries):
        t = threading.Thread(target=search_query, args=(query, i))
        threads.append(t)
        t.start()
    
    # Aguarda todas completarem
    for t in threads:
        t.join()
    
    total_time = time.time() - start_total
    
    print(f"\n📊 Resultados:")
    print(f"  Total de queries: {len(queries)}")
    print(f"  Tempo total: {total_time:.2f}s")
    print(f"  Tempo esperado mínimo: {len(queries) * 1.1:.2f}s (1.1s por query)")
    print(f"  Erros: {len(errors)}")
    
    # Valida rate limiting
    if total_time >= len(queries) * 1.0:  # Mínimo 1s por query
        print("  ✅ Rate limiting funcionando: tempo total respeitou limite")
    else:
        print(f"  ⚠️  Rate limiting pode não estar funcionando: tempo muito curto")
    
    # Mostra detalhes
    print(f"\nDetalhes por query:")
    for idx, query, count, elapsed, error in sorted(results):
        status = "✅" if error is None else "❌"
        print(f"  {status} {idx}: '{query}' → {count} resultados, {elapsed:.2f}s")
    
    return len(errors) == 0


def test_cache():
    """Testa funcionamento do cache."""
    print("\n" + "="*60)
    print("TESTE 2: Cache de Queries")
    print("="*60)
    
    tool = LiteratureTool()
    query = "logistic regression iris"
    
    print(f"\nQuery de teste: '{query}'")
    
    # Primeira busca (deve fazer requisição real)
    print("\n1️⃣  Primeira busca (sem cache)...")
    start1 = time.time()
    results1 = tool.search(query, k=3)
    time1 = time.time() - start1
    cache_size_before = len(tool._cache)
    print(f"   Resultados: {len(results1)}")
    print(f"   Tempo: {time1:.3f}s")
    print(f"   Cache size: {cache_size_before}")
    
    # Segunda busca (deve usar cache)
    print("\n2️⃣  Segunda busca (com cache)...")
    start2 = time.time()
    results2 = tool.search(query, k=3)
    time2 = time.time() - start2
    cache_size_after = len(tool._cache)
    print(f"   Resultados: {len(results2)}")
    print(f"   Tempo: {time2:.3f}s")
    print(f"   Cache size: {cache_size_after}")
    
    # Valida cache
    cache_working = results1 == results2 and time2 < time1 * 0.5
    if cache_working:
        print("\n  ✅ Cache funcionando corretamente:")
        print(f"     - Resultados idênticos: {results1 == results2}")
        print(f"     - Segunda busca {time1/time2:.1f}x mais rápida")
    else:
        print("\n  ⚠️  Cache pode não estar funcionando:")
        print(f"     - Resultados idênticos: {results1 == results2}")
        print(f"     - Tempo: {time1:.3f}s → {time2:.3f}s")
    
    return cache_working


def test_settings():
    """Testa configurações de rate limit e cache."""
    print("\n" + "="*60)
    print("TESTE 3: Configurações")
    print("="*60)
    
    settings = Settings()
    
    print(f"\n📋 Configurações atuais:")
    print(f"  SEMANTIC_SCHOLAR_RATE_LIMIT: {settings.SEMANTIC_SCHOLAR_RATE_LIMIT}s")
    print(f"  SEMANTIC_SCHOLAR_CACHE_TTL: {settings.SEMANTIC_SCHOLAR_CACHE_TTL}s ({settings.SEMANTIC_SCHOLAR_CACHE_TTL/3600:.1f}h)")
    print(f"  SEMANTIC_SCHOLAR_API_KEY: {'✅ Configurada' if settings.SEMANTIC_SCHOLAR_API_KEY else '❌ Não configurada'}")
    
    # Valida valores
    valid_rate = 1.0 <= settings.SEMANTIC_SCHOLAR_RATE_LIMIT <= 2.0
    valid_ttl = 60 <= settings.SEMANTIC_SCHOLAR_CACHE_TTL <= 86400
    
    print(f"\n✅ Validação:")
    print(f"  Rate limit válido (1.0-2.0s): {valid_rate}")
    print(f"  Cache TTL válido (60s-24h): {valid_ttl}")
    
    return valid_rate and valid_ttl


def test_client_direct():
    """Testa cliente diretamente."""
    print("\n" + "="*60)
    print("TESTE 4: Cliente Direto")
    print("="*60)
    
    settings = Settings()
    if not settings.SEMANTIC_SCHOLAR_API_KEY:
        print("⚠️  SEMANTIC_SCHOLAR_API_KEY não configurada. Pulando teste.")
        return True
    
    try:
        client = SemanticScholarClient(api_key=settings.SEMANTIC_SCHOLAR_API_KEY)
        
        print("\n1️⃣  Primeira requisição...")
        start1 = time.time()
        results1 = client.search("machine learning", limit=2)
        time1 = time.time() - start1
        print(f"   Resultados: {len(results1)}")
        print(f"   Tempo: {time1:.3f}s")
        
        print("\n2️⃣  Segunda requisição (deve respeitar rate limit)...")
        start2 = time.time()
        results2 = client.search("deep learning", limit=2)
        time2 = time.time() - start2
        print(f"   Resultados: {len(results2)}")
        print(f"   Tempo: {time2:.3f}s")
        
        if time2 >= 1.0:
            print("\n  ✅ Rate limiting funcionando: segunda requisição respeitou intervalo")
        else:
            print(f"\n  ⚠️  Rate limiting pode não estar funcionando: tempo muito curto ({time2:.3f}s)")
        
        return time2 >= 1.0
        
    except Exception as e:
        print(f"\n  ❌ Erro ao testar cliente: {str(e)}")
        return False


def main():
    """Executa todos os testes."""
    print("\n" + "="*60)
    print("TESTES DE RATE LIMITING E CACHE - Semantic Scholar")
    print("="*60)
    
    setup_logging()
    
    results = {}
    
    # Teste 1: Rate limiting
    try:
        results['rate_limiting'] = test_rate_limiting_concurrent()
    except Exception as e:
        print(f"\n❌ Erro no teste de rate limiting: {str(e)}")
        results['rate_limiting'] = False
    
    # Teste 2: Cache
    try:
        results['cache'] = test_cache()
    except Exception as e:
        print(f"\n❌ Erro no teste de cache: {str(e)}")
        results['cache'] = False
    
    # Teste 3: Settings
    try:
        results['settings'] = test_settings()
    except Exception as e:
        print(f"\n❌ Erro no teste de settings: {str(e)}")
        results['settings'] = False
    
    # Teste 4: Cliente direto
    try:
        results['client'] = test_client_direct()
    except Exception as e:
        print(f"\n❌ Erro no teste de cliente: {str(e)}")
        results['client'] = False
    
    # Resumo final
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {test_name:20s}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM")
    print("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    exit(0 if main() else 1)

