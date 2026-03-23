import pandas as pd
from dotenv import load_dotenv

from langchain.tools import Tool
from langchain_openai import ChatOpenAI
#from langchain_anthropic import ChatAnthropic
from langchain_experimental.agents import create_pandas_dataframe_agent

load_dotenv()

# Initialize LLM
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
#model = ChatAnthropic(model="claude-3-5-sonnet-latest", temperature=0, api_key=user_secrets.get_secret("my-anthropic-api-key"))

# Load the Titanic dataset
df = pd.read_csv("src/agents/sheet_analyzer/doc/titanic.csv")

# Define a custom tool
def custom_calculation_tool(input: str) -> str:
    return f"Custom calculation result for: {input}"
    
# Add the custom tool to the agent
extra_tools = [
    Tool(
        name="custom_calculation",
        func=custom_calculation_tool,
        description="A tool for performing custom calculations."
    )
]

# Create the agent with default parameters
agent = create_pandas_dataframe_agent(
    llm=model,
    df=df,
    agent_type="tool-calling",  # Use the modern "tool-calling" agent type
    extra_tools=extra_tools,  # Add custom tools

    prefix="You are a data analyst. Analyze the Titanic dataset and provide concise answers.",
    suffix="Provide the final answer in a clear and structured format.",

    include_df_in_prompt=True,  # Include the DataFrame head in the prompt
    number_of_head_rows=5,      # Number of rows to include

    max_execution_time=10,  # Limit execution time to 10 seconds
    #max_iterations=5,       # Limit the number of iterations to 5
    early_stopping_method="force",  # Force stop on errors

    allow_dangerous_code=True,  # Allow execution of Python code (use with caution)
    verbose=True,               # Enable verbose logging for debugging
)

if __name__ == "__main__":
    import json

    # Ask the agent a question
    response = agent.invoke("Create a bar chart showing the number of passengers in each class.")

    print(f"\nResponse:\n{json.dumps(response, indent=4)}")
    print(f"\nOutput: {response["output"]}\n")






