"""
Teste rápido de rate limiting e cache (versão simplificada).
"""
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.literature import LiteratureTool
from src.config.settings import Settings
import structlog

# Configura logging mínimo
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.KeyValueRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
)

def main():
    print("="*60)
    print("TESTE RÁPIDO: Rate Limiting e Cache")
    print("="*60)
    
    settings = Settings()
    print(f"\n📋 Configurações:")
    print(f"  Rate Limit: {settings.SEMANTIC_SCHOLAR_RATE_LIMIT}s")
    print(f"  Cache TTL: {settings.SEMANTIC_SCHOLAR_CACHE_TTL}s")
    print(f"  API Key: {'✅' if settings.SEMANTIC_SCHOLAR_API_KEY else '❌'}")
    
    tool = LiteratureTool()
    
    # Teste 1: Cache
    print("\n" + "-"*60)
    print("TESTE 1: Cache")
    print("-"*60)
    
    query = "logistic regression"
    print(f"\nQuery: '{query}'")
    
    # Primeira busca
    print("\n1️⃣  Primeira busca (sem cache)...")
    start1 = time.time()
    r1 = tool.search(query, k=2)
    t1 = time.time() - start1
    print(f"   ✅ {len(r1)} resultados em {t1:.3f}s")
    print(f"   Cache size: {len(tool._cache)}")
    
    # Segunda busca (cache)
    print("\n2️⃣  Segunda busca (com cache)...")
    start2 = time.time()
    r2 = tool.search(query, k=2)
    t2 = time.time() - start2
    print(f"   ✅ {len(r2)} resultados em {t2:.3f}s")
    
    cache_ok = r1 == r2 and t2 < t1 * 0.5
    print(f"\n   {'✅ Cache funcionando' if cache_ok else '⚠️ Cache pode não estar funcionando'}")
    if cache_ok:
        print(f"   Speedup: {t1/t2:.1f}x mais rápido")
    
    # Teste 2: Rate limiting (2 requisições sequenciais)
    print("\n" + "-"*60)
    print("TESTE 2: Rate Limiting")
    print("-"*60)
    
    if settings.SEMANTIC_SCHOLAR_API_KEY and tool._s2:
        print("\nExecutando 2 requisições sequenciais...")
        
        q1 = "machine learning"
        print(f"\n1️⃣  Query: '{q1}'")
        start1 = time.time()
        r1 = tool.search(q1, k=2)
        t1 = time.time() - start1
        print(f"   ✅ {len(r1)} resultados em {t1:.3f}s")
        
        q2 = "deep learning"
        print(f"\n2️⃣  Query: '{q2}'")
        start2 = time.time()
        r2 = tool.search(q2, k=2)
        t2 = time.time() - start2
        print(f"   ✅ {len(r2)} resultados em {t2:.3f}s")
        
        rate_ok = t2 >= 1.0
        print(f"\n   {'✅ Rate limiting funcionando' if rate_ok else '⚠️ Rate limiting pode não estar funcionando'}")
        if rate_ok:
            print(f"   Intervalo respeitado: {t2:.3f}s >= 1.0s")
        else:
            print(f"   Intervalo muito curto: {t2:.3f}s < 1.0s")
    else:
        print("\n⚠️  API key não configurada. Pulando teste de rate limiting.")
        rate_ok = None
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO")
    print("="*60)
    print(f"  Cache: {'✅ OK' if cache_ok else '⚠️ Verificar'}")
    if rate_ok is not None:
        print(f"  Rate Limiting: {'✅ OK' if rate_ok else '⚠️ Verificar'}")
    print("="*60 + "\n")
    
    return cache_ok and (rate_ok if rate_ok is not None else True)

if __name__ == "__main__":
    exit(0 if main() else 1)

