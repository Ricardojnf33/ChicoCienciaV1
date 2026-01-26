from src.config.settings import Settings
from src.agents.researcher import researcher
from src.tools.literature import LiteratureTool
import os

def test():
    settings = Settings()
    print(f"Testing with Model: {settings.MODEL_TEXT}")
    print(f"OpenAI Key set: {settings.OPENAI_API_KEY is not None}")
    
    # Test Literature Tool
    tool = LiteratureTool()
    print("Testing Literature Tool...")
    res = tool.search("logistic regression iris", k=2)
    print(f"Found {len(res)} papers.")
    for p in res:
        print(f" - {p['title']} ({p['year']})")

if __name__ == "__main__":
    test()
