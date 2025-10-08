import time
from typing import List, Dict, Any
from arxiv import Search, SortOrder


class ArxivClient:
    def __init__(self, max_results: int = 5, delay_s: float = 0.0):
        self.max_results = max_results
        self.delay_s = delay_s

    def search(self, query: str) -> List[Dict[str, Any]]:
        if self.delay_s:
            time.sleep(self.delay_s)
        results = []
        search = Search(query=query, max_results=self.max_results, sort_by=SortOrder.Relevance)
        for res in search.results():
            results.append({
                "title": res.title,
                "year": res.published.year if res.published else None,
                "url": res.entry_id,
                "summary": res.summary,
                "source": "arxiv",
            })
        return results


