#!/usr/bin/env python3
"""
Script de monitoramento de rate limiting do Semantic Scholar.

Uso:
    python scripts/monitor_rate_limiting.py [--verbose] [--queries N]

Monitora chamadas à API e valida que o rate limiting está funcionando.
"""
import argparse
import time
import sys
import os
from pathlib import Path

# Adiciona raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tools.literature import LiteratureTool
from src.config.settings import Settings
import structlog


def setup_logging(verbose: bool = False):
    """Configura logging estruturado."""
    level = 10 if verbose else 20  # DEBUG se verbose, INFO caso contrário
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.KeyValueRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
    )


def monitor_queries(num_queries: int = 5, verbose: bool = False):
    """Monitora execução de queries e valida rate limiting."""
    settings = Settings()
    
    print("="*70)
    print("MONITORAMENTO DE RATE LIMITING - Semantic Scholar")
    print("="*70)
    
    print(f"\n📋 Configurações:")
    print(f"  Rate Limit: {settings.SEMANTIC_SCHOLAR_RATE_LIMIT}s")
    print(f"  Cache TTL: {settings.SEMANTIC_SCHOLAR_CACHE_TTL}s")
    print(f"  API Key: {'✅ Configurada' if settings.SEMANTIC_SCHOLAR_API_KEY else '❌ Não configurada'}")
    
    if not settings.SEMANTIC_SCHOLAR_API_KEY:
        print("\n⚠️  API key não configurada. Monitoramento limitado.")
        return
    
    tool = LiteratureTool()
    
    queries = [
        "machine learning",
        "deep learning",
        "neural networks",
        "transformer architecture",
        "reinforcement learning",
        "computer vision",
        "natural language processing",
        "reinforcement learning",
    ][:num_queries]
    
    print(f"\n🔍 Executando {len(queries)} queries sequenciais...")
    print("-"*70)
    
    timings = []
    cache_hits = 0
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] Query: '{query}'")
        
        start = time.time()
        try:
            results = tool.search(query, k=3)
            elapsed = time.time() - start
            
            timings.append(elapsed)
            
            # Verifica se foi cache hit (tempo muito rápido)
            is_cache_hit = elapsed < 0.1
            if is_cache_hit:
                cache_hits += 1
            
            status = "💾 CACHE" if is_cache_hit else "🌐 API"
            print(f"  {status} → {len(results)} resultados em {elapsed:.3f}s")
            
            if verbose and results:
                print(f"  Primeiro resultado: {results[0].get('title', 'N/A')[:60]}...")
                
        except Exception as e:
            elapsed = time.time() - start
            timings.append(elapsed)
            print(f"  ❌ ERRO: {str(e)} ({elapsed:.3f}s)")
    
    # Análise
    print("\n" + "="*70)
    print("ANÁLISE")
    print("="*70)
    
    if timings:
        total_time = sum(timings)
        avg_time = total_time / len(timings)
        min_time = min(timings)
        max_time = max(timings)
        
        # Separa requisições de API vs cache
        api_timings = [t for t in timings if t >= 0.1]
        cache_timings = [t for t in timings if t < 0.1]
        
        print(f"\n⏱️  Tempos:")
        print(f"  Total: {total_time:.2f}s")
        print(f"  Média: {avg_time:.3f}s")
        print(f"  Mínimo: {min_time:.3f}s")
        print(f"  Máximo: {max_time:.3f}s")
        
        print(f"\n📊 Distribuição:")
        print(f"  Requisições API: {len(api_timings)}")
        print(f"  Cache hits: {len(cache_timings)}")
        
        if api_timings:
            avg_api_time = sum(api_timings) / len(api_timings)
            print(f"  Tempo médio API: {avg_api_time:.3f}s")
            
            # Valida rate limiting
            if len(api_timings) > 1:
                intervals = [api_timings[i] - api_timings[i-1] for i in range(1, len(api_timings))]
                min_interval = min(intervals) if intervals else 0
                print(f"  Intervalo mínimo entre APIs: {min_interval:.3f}s")
                
                rate_limit_ok = min_interval >= 1.0
                print(f"\n  {'✅ Rate limiting OK' if rate_limit_ok else '⚠️ Rate limiting pode estar falhando'}")
        
        print(f"\n💾 Cache:")
        print(f"  Hits: {cache_hits}/{len(queries)} ({cache_hits/len(queries)*100:.1f}%)")
        cache_working = cache_hits > 0
        print(f"  {'✅ Cache funcionando' if cache_working else '⚠️ Cache pode não estar funcionando'}")
    
    print("\n" + "="*70)


def main():
    parser = argparse.ArgumentParser(description="Monitora rate limiting do Semantic Scholar")
    parser.add_argument("--queries", "-q", type=int, default=5, help="Número de queries para testar")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verbose (DEBUG logs)")
    args = parser.parse_args()
    
    setup_logging(verbose=args.verbose)
    monitor_queries(num_queries=args.queries, verbose=args.verbose)


if __name__ == "__main__":
    main()

