from src.agents import manager as manager_module


def test_build_manager_does_not_attach_tools_explicitly(monkeypatch):
    """CrewAI hierarchical managers must receive delegation, not a tools field."""
    captured = {}

    class CapturingAgent:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(manager_module, "Agent", CapturingAgent)

    manager = manager_module.build_manager(object())

    assert isinstance(manager, CapturingAgent)
    assert captured["allow_delegation"] is True
    assert "tools" not in captured
