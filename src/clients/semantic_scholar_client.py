from typing import List, Dict, Any
from semanticscholar import SemanticScholar


class SemanticScholarClient:
    def __init__(self, api_key: str | None = None, timeout: int = 20):
        self.client = SemanticScholar(api_key=api_key, timeout=timeout)

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        # fields: title, year, url (openAccessPdf or external ids)
        papers = self.client.search_paper(query=query, limit=limit)
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
        return results


