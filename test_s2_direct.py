from semanticscholar import SemanticScholar
import os
from src.config.settings import Settings

def test():
    settings = Settings()
    s2 = SemanticScholar(api_key=settings.SEMANTIC_SCHOLAR_API_KEY, timeout=20)
    print("Directly calling SemanticScholar SDK...")
    results = s2.search_paper(query="logistic regression iris", limit=2)
    print(f"Got {len(results)} results.")

if __name__ == "__main__":
    test()
