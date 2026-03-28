from dataclasses import dataclass, field

@dataclass
class AgentConfig:
    model_id: str = "gpt-4.1-mini"

@dataclass
class GenereteDocStringConfig:
    instructions: str = """

    """

    description: str = """

    """

@dataclass
class GenereteDocClassConfig:
    instructions: str = """

    """

    description: str = """

    """