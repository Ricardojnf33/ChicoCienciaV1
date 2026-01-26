from src.clients.arxiv_client import ArxivClient

def test():
    client = ArxivClient()
    print("Testing ArXiv Client...")
    res = client.search("logistic regression iris")
    print(f"Found {len(res)} papers.")
    for p in res:
        print(f" - {p['title']}")

if __name__ == "__main__":
    test()
