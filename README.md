# BetterAI — Where Intelligence Finds Purpose

![BetterAI](<images/Frame 27346.png>)

# Múltiplos Modelos de IA, Um Único Back-end de IA Unificado

A BetterAI é uma plataforma desenvolvida para tornar a inteligência artificial **prática, escalável e acessível** para aplicações do mundo real.

Em vez de construir uma infraestrutura complexa de IA do zero, a BetterAI oferece uma base sólida que permite às equipes integrar recursos inteligentes diretamente em seus sistemas, fluxos de trabalho e produtos.

Da análise de documentos à exploração avançada de dados, a BetterAI permite que organizações transformem dados em **inteligência acionável**.

A BetterAI reúne diversos modelos especializados de IA em uma única plataforma, projetada para gerar impacto real nos negócios.

Em vez de depender de um único tipo de inteligência artificial, a BetterAI oferece um ecossistema diversificado de recursos de IA que trabalham juntos de forma integrada.

Essa abordagem unificada permite que as organizações:

* Extraiam insights dos dados
* Automatizem fluxos de trabalho complexos
* Gerem conteúdo em diversos formatos
* Apoiem a tomada de decisões com sistemas inteligentes

Tudo isso a partir de uma **única plataforma de IA integrada**.

**Autor:** Enzo Schitini



## **Guia de Inicialização**

### **1. Atualize o Projeto**

Primeiro, certifique-se de estar na branch correta e de que o seu código está atualizado:

```
git checkout main
git pull
git checkout -b nome-da-sua-branch
```

---

### **2. Crie o Ambiente Virtual**

> **Requisito:** Python 3.14 ou superior (versão fixada em `.python-version`).
> 

Crie um ambiente virtual para isolar as dependências do projeto:

```
python -m venv .venv
```

---

### **3. Ative o Ambiente Virtual**

#### **PowerShell**

```
.\.venv\Scripts\Activate.ps1
```

#### **CMD**

```
.venv\Scripts\activate.bat
```

Após a ativação, o seu terminal deve ficar parecido com isto:

```
(.venv) PS C:\Users\nome_do_usuario\personal-finances>
```

---

### **4. Instale as Dependências**

Você pode instalar as dependências de duas formas:

#### **Usando uv (recomendado)**

```
uv sync
```

---

### **5. Configure as Variáveis de Ambiente**

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

| **Variável** | **Descrição** |
| --- | --- |
| `BETTERAI_API_KEY` | Chave de API interna da BetterAI |
| `OPENAI_API_KEY` | Chave de API da OpenAI |
| `OPENAI_EMBEDDING_MODEL` | Modelo de embeddings da OpenAI utilizado |
| `GEMINI_API_KEY` | Chave de API do Google Gemini |
| `GROQ_API_KEY` | Chave de API da Groq |
| `ANTHROPIC_API_KEY` | Chave de API da Anthropic (Claude) |
| `TAVILY_API_KEY` | Chave de API do Tavily (busca web) |
| `FAL_API_KEY` | Chave de API do Fal (geração de mídia) |
| `EXCHANGE_RATE_API_KEY` | Chave de API de cotação de câmbio |
| `HUGGINGFACEHUB_API_TOKEN` | Token de acesso ao Hugging Face Hub |
| `PINECONE_API_KEY` | Chave de API do Pinecone (vector store) |
| `PINECONE_ENVIRONMENT` | Região/ambiente do Pinecone |
| `PINECONE_INDEX_NAME` | Nome do índice vetorial no Pinecone |
| `PINECONE_NAMESPACE` | Namespace da base de conhecimento |
| `PINECONE_GLOBAL_NAMESPACE` | Namespace global da base de conhecimento |
| `MONGO_URI` | String de conexão completa do MongoDB |
| `MONGO_USER` | Usuário do MongoDB |
| `MONGO_PASSWORD` | Senha do MongoDB |
| `MONGO_HOST` | Host do MongoDB |
| `MONGO_PORT` | Porta do MongoDB |
| `NOSQL_BACKEND` | Backend NoSQL utilizado (`local` ou remoto) |
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_SECRET_KEY` | Chave secreta de serviço do Supabase |
| `SUPABASE_DATABASE_URL` | String de conexão do banco Postgres do Supabase |
| `SUPABASE_PROJECT_NAME` | Nome do projeto Supabase |
| `SUPABASE_PROJECT_HOST` | Host do projeto Supabase |
| `SUPABASE_DATABASE_PASSWORD` | Senha do banco de dados Supabase |
| `SHOW_INFO_LOGS` | Exibe logs informativos (`true`/`false`) |
| `SHOW_METADATA` | Exibe metadados nas respostas (`true`/`false`) |
| `FORMAT_METADATA` | Formata os metadados exibidos (`true`/`false`) |
| `SAVE_LOGS` | Salva logs de execução (`true`/`false`) |
| `SAVE_MONGO` | Salva dados de execução no MongoDB (`true`/`false`) |
| `LOCAL` | Flag para execução local (`true`/`false`) |

```
# BetterAI
BETTERAI_API_KEY=********************

# LLM's
OPENAI_API_KEY=********************
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

GEMINI_API_KEY=********************
GROQ_API_KEY=********************
ANTHROPIC_API_KEY=********************

# Tools
TAVILY_API_KEY=********************
FAL_API_KEY=********************
EXCHANGE_RATE_API_KEY=********************
HUGGINGFACEHUB_API_TOKEN=********************

# Database

# Pinecone
PINECONE_API_KEY=********************
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=backai-vectorstore
PINECONE_NAMESPACE=knowledge_base_content_agent_oboticario2
PINECONE_GLOBAL_NAMESPACE=global_knowledge_base_content_agent2

# MongoDB
MONGO_URI=********************
MONGO_USER=********************
MONGO_PASSWORD=********************
MONGO_HOST=********************
MONGO_PORT=********************

NOSQL_BACKEND=local

# Supabase
SUPABASE_URL=********************
SUPABASE_SECRET_KEY=********************
SUPABASE_DATABASE_URL=********************
SUPABASE_PROJECT_NAME=better-ai-bucket-storage
SUPABASE_PROJECT_HOST=********************
SUPABASE_DATABASE_PASSWORD=********************

# Application Tracing Rules
SHOW_INFO_LOGS=false
SHOW_METADATA=false
FORMAT_METADATA=false
SAVE_LOGS=false
SAVE_MONGO=false

LOCAL=false
```

---

### **6. Execute a aplicação**

Com o ambiente virtual ativado e as dependências instaladas, inicie a aplicação Streamlit:

```
streamlit run app.py
```

A aplicação ficará disponível em http://localhost:8501.





--- 
![BetterAI](<images/Frame 27346.png>)
![alt text](<images/Gemini_Generated_Image_12swry12swry12sw (1).png>)
![alt text](images/Gemini_Generated_Image_hhqir9hhqir9hhqi.png)
![alt text](images/Gemini_Generated_Image_mmbn14mmbn14mmbn.png)
---

