# Update version

O langchain principal passou da 0.3.27 para a 1.5.0, ou seja, da série 0.3 para a 1.x. Os números vêm do git diff de pyproject.toml e de uv.lock, e o lock mostra as versões que ficaram instaladas de fato.

| Pacote | Antes | Depois |
|---|---|---|
| langchain | 0.3.27 | 1.5.0 |
| langchain-core | 0.3.81 | 1.8.2 |
| langchain-community | 0.3.31 | 0.4.2 |
| langchain-experimental | 0.3.4 | 0.4.2 |
| langchain-openai | 0.3.35 | 1.1.9 |
| langchain-google-genai | 2.1.12 | 4.5.0 |
| langchain-groq | 0.3.8 | 1.2.0 |
| langchain-text-splitters | 0.3.11 | 1.1.3 |

Também entraram pacotes novos: langchain-classic (1.0.8), langchain-anthropic (1.7.10) e deepagents.

# Com o update quebraram alguns módulos antigos:

## Agents

- src\agents\langchain_tool_agent\agent_executor.py

## Chat

- src\chat\tools\retrieval.py
- src\chat\tools\tools.py
- src\chat\buffer_memory.py
- src\chat\InitializeAgent.py

## Dataframe Analyzers

- src\dataframe_analyzers\pd_df_agent\agent.py

## Vector Store

src\vector_store\pinecone\embedding.py