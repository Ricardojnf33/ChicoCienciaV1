from crewai import Crew, Process
from langchain_openai import ChatOpenAI

from src.agents.coder import build_coder
from src.agents.manager import build_manager
from src.agents.researcher import build_researcher
from src.agents.reviewer import build_reviewer
from src.agents.vlm_critic import build_vlm_critic
from src.config.settings import Settings


def build_crew(settings: Settings | None = None) -> Crew:
    resolved = settings or Settings()
    api_key = resolved.require_openai_api_key()
    text_llm = ChatOpenAI(
        model=resolved.MODEL_TEXT,
        api_key=api_key,
        temperature=0,
    )
    vision_llm = ChatOpenAI(
        model=resolved.MODEL_VISION,
        api_key=api_key,
        temperature=0,
    )
    manager = build_manager(text_llm)
    agents = [
        build_researcher(text_llm),
        build_coder(text_llm),
        build_reviewer(text_llm),
        build_vlm_critic(vision_llm),
    ]
    return Crew(
        agents=agents,
        process=Process.hierarchical,
        manager_agent=manager,
        verbose=True,
    )
