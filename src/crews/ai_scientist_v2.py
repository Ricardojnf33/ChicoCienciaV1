from pathlib import Path

from crewai import Crew, Process
from langchain_openai import ChatOpenAI

from src.agents.coder import build_coder
from src.agents.manager import build_manager
from src.agents.researcher import build_researcher
from src.agents.reviewer import build_reviewer
from src.agents.vlm_critic import build_vlm_critic
from src.config.settings import Settings
from src.core.llm_budget import BudgetCallbackHandler, LLMBudgetLedger


def build_crew(
    settings: Settings | None = None,
    *,
    budget_path: str | Path | None = None,
) -> Crew:
    resolved = settings or Settings()
    api_key = resolved.require_openai_api_key()
    ledger = LLMBudgetLedger(
        model=resolved.MODEL_TEXT,
        token_limit=resolved.LLM_TOKEN_LIMIT,
        cost_limit_usd=resolved.LLM_COST_LIMIT_USD,
        max_output_tokens_per_call=resolved.LLM_MAX_OUTPUT_TOKENS,
        input_per_million_usd=resolved.LLM_INPUT_PER_MILLION_USD,
        cached_input_per_million_usd=resolved.LLM_CACHED_INPUT_PER_MILLION_USD,
        output_per_million_usd=resolved.LLM_OUTPUT_PER_MILLION_USD,
        journal_path=budget_path,
    )
    budget_callback = BudgetCallbackHandler(ledger)
    text_llm = ChatOpenAI(
        model=resolved.MODEL_TEXT,
        api_key=api_key,
        temperature=0,
        max_tokens=resolved.LLM_MAX_OUTPUT_TOKENS,
        callbacks=[budget_callback],
    )
    vision_llm = ChatOpenAI(
        model=resolved.MODEL_VISION,
        api_key=api_key,
        temperature=0,
        max_tokens=resolved.LLM_MAX_OUTPUT_TOKENS,
        callbacks=[budget_callback],
    )
    manager = build_manager(text_llm)
    agents = [
        build_researcher(text_llm),
        build_coder(text_llm),
        build_reviewer(text_llm),
        build_vlm_critic(vision_llm),
    ]
    crew = Crew(
        agents=agents,
        process=Process.hierarchical,
        manager_agent=manager,
        verbose=True,
    )
    object.__setattr__(crew, "_chico_llm_budget", ledger)
    return crew


def budget_for_crew(crew: Crew) -> LLMBudgetLedger:
    try:
        return crew._chico_llm_budget
    except AttributeError as exc:
        raise ValueError("Crew sem orçamento LLM fail-closed.") from exc
