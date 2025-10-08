from crewai import Agent

ethics_guard = Agent(
    role="Ethics Guard",
    goal="Aplicar checklist de ética, licenças e transparência; pedir humano se necessário.",
    verbose=True,
)
