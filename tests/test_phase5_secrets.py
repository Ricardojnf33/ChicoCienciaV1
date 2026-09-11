import os
from importlib.metadata import version

import pytest
from packaging.version import Version

from src.config.settings import Settings


def test_openai_key_is_masked_by_settings():
    value = "sk-test-phase5-never-send"
    settings = Settings(OPENAI_API_KEY=value, _env_file=None)

    assert settings.require_openai_api_key() == value
    assert value not in repr(settings)
    assert value not in settings.model_dump_json()


def test_crew_receives_key_explicitly_without_exporting_it(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    for name in (
        "ALL_PROXY",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "all_proxy",
        "http_proxy",
        "https_proxy",
    ):
        monkeypatch.delenv(name, raising=False)
    import tiktoken

    class OfflineEncoding:
        def encode(self, text):
            return list(text.encode())

    monkeypatch.setattr(tiktoken, "encoding_for_model", lambda model: OfflineEncoding())
    monkeypatch.setattr(tiktoken, "get_encoding", lambda name: OfflineEncoding())
    settings = Settings(
        OPENAI_API_KEY="sk-test-explicit-injection",
        MODEL_TEXT="gpt-4.1-mini",
        MODEL_VISION="gpt-4o-mini",
        _env_file=None,
    )

    from crewai import Agent, Crew
    from src.crews.ai_scientist_v2 import build_crew

    crew = build_crew(settings)

    assert isinstance(crew, Crew)
    assert isinstance(crew.manager_agent, Agent)
    assert all(isinstance(agent, Agent) for agent in crew.agents)
    assert [agent.llm.model_name for agent in crew.agents] == [
        "gpt-4.1-mini",
        "gpt-4.1-mini",
        "gpt-4.1-mini",
        "gpt-4o-mini",
    ]
    assert "OPENAI_API_KEY" not in os.environ


def test_crew_rejects_absent_key_before_agent_construction():
    from src.crews.ai_scientist_v2 import build_crew

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        build_crew(Settings(_env_file=None))


def test_crewai_compatibility_dependency_retains_pkg_resources():
    assert Version(version("setuptools")) < Version("81")
    __import__("pkg_resources")
