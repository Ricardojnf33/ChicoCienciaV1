from crewai import Agent

data_steward = Agent(
    role="Data Steward",
    goal="Garantir versionamento de dados, seeds e replicabilidade.",
    verbose=True,
)
