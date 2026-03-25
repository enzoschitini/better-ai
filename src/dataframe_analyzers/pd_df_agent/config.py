from dataclasses import dataclass, field

@dataclass
class AgentConfig:
    id_model: str = "gpt-4o-mini"
    model_provider: str = "openai"
    # "gpt-4o-mini" "gpt-5.2" "gemini-2.5-flash"
    temperature: int = 0

    agent_type: str = "tool-calling"

    include_df_in_prompt: bool = True
    number_of_head_rows: int = 5
    
    max_execution_time: int = 60
    early_stopping_method: str = "force"

    allow_dangerous_code: bool = True
    verbose: bool = True

    prefix: str = """
    You are a data analyst working with a pandas DataFrame called `df`.

    Rules:
    - ALWAYS use the provided dataframe `df`
    - NEVER load external datasets

    When creating plots:
    - ALWAYS use matplotlib
    - ALWAYS call plt.show() at the end
    - ALWAYS frame the information within the graph image so that text and numbers are not cut off.
    """

    suffix: str = """
    Provide the final answer clearly.

    IMPORTANT:
    - Do NOT include any image links, file paths, or markdown images
    - Do NOT mention where the chart is saved
    - Assume the chart is already displayed in the interface
    - Only describe the insights from the chart
    """
