# Web Service Network - API

A **BetterAI Web Service Network** é uma API modular de alto desempenho projetada para orquestrar serviços de inteligência artificial em produção. Ela expõe um conjunto de routers especializados — pesquisa profunda na web, parsing de documentos, geração de imagens e gerenciamento de vector stores — todos acessíveis via HTTP com autenticação por chave de API.

A API é construída sobre **FastAPI** e servida com **Uvicorn**, oferecendo documentação interativa automática via Swagger UI (`/docs`) e suporte nativo a requisições assíncronas. Cada endpoint retorna respostas padronizadas com `job_id`, `status`, `result` e métricas de tempo de execução, facilitando rastreabilidade e integração com pipelines de dados.

**Base URL:** `http://localhost:8000`  
**Autenticação:** `X-API-Key` no header de todas as rotas protegidas  
**Versão atual:** `1.0.0`

[🌐 Domain](http://localhost:8000) · [🩺 Health](http://localhost:8000/health) · [📄 Documentation](http://localhost:8000/docs)

### Start application

```bash
# uvicorn web_services:app --reload
```

```bash
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [8036] using StatReload
INFO:     Router included: /davinci
INFO:     Router included: /deep-research
INFO:     Router included: /parse-content
INFO:     Router included: /vector-store
INFO:     Started server process [30416]
INFO:     Waiting for application startup.
INFO:     

    ╔═══════════════════════════════════════════════════════════════════════╗

        ██████╗ ███████╗████████╗████████╗███████╗██████╗      █████╗ ██╗ ✦
        ██╔══██╗██╔════╝╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗    ██╔══██╗██║
        ██████╔╝█████╗     ██║      ██║   █████╗  ██████╔╝    ███████║██║
        ██╔══██╗██╔══╝     ██║      ██║   ██╔══╝  ██╔══██╗    ██╔══██║██║
        ██████╔╝███████╗   ██║      ██║   ███████╗██║  ██║    ██║  ██║██║
        ╚═════╝ ╚══════╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝

    ╚═══════════════════════════════════════════════════════════════════════╝

                        ✦ Where intelligence finds purpose. ✦
    
INFO:     BetterAI Web Service Network initialized successfully at 2026-05-21 16:19:25.
INFO:     Version: 1.0.0
INFO:     Domain: http://localhost:8000
INFO:     Health check available at: http://localhost:8000/health
INFO:     Documentation available at: http://localhost:8000/docs
INFO:     Application startup complete.
```

# Routers

## 1. Healthy - */healthy*

```bash
curl -X GET "http://127.0.0.1:8000/health"
```

## 2. Healthy With Authorization - */health-authorization*

```bash
curl --location 'http://localhost:8000/health-authorization' \
--header 'X-API-Key: ******'
```



## 3. Context Builder - */deep-research/context-builder*

Constrói um contexto rico em markdown a partir de uma pesquisa profunda na web, usando o **TavilyDeepResearch** como motor de busca. Ideal para alimentar pipelines de RAG, geração de relatórios ou enriquecimento de prompts.

### Parâmetros

| Parâmetro | Tipo | Descrição | Exemplo |
|---|---|---|---|
| `query` | `string` | Pergunta ou tema central da pesquisa. Define o que será buscado. | `"Principais tendências de IA em 2026?"` |
| `search_depth` | `"basic"` \| `"advanced"` | Profundidade da busca. `basic` para uma visão rápida, `advanced` para uma pesquisa mais abrangente e detalhada. | `"advanced"` |
| `max_results` | `integer` (1–100) | Número máximo de resultados a recuperar e incluir no contexto. | `35` |
| `topic` | `string` | Categoria ou domínio da pesquisa. Orienta o tipo de fonte priorizada. Valores comuns: `general`, `news`, `finance`. | `"news"` |
| `include_answer` | `boolean` | Se `true`, inclui no contexto uma resposta gerada automaticamente com base nos resultados encontrados. | `true` |
| `min_score` | `float` (0.0–1.0) | Score mínimo de relevância. Resultados abaixo desse limiar são descartados. Valores mais altos = contexto mais preciso, porém menor. | `0.5` |

### Request

```bash
curl --location 'http://localhost:8000/deep-research/context-builder' \
--header 'Content-Type: application/json' \
--header 'X-API-Key: ******' \
--data '{
    "query": "Principais tendências de IA em 2026?",
    "search_depth": "advanced",
    "max_results": 35,
    "topic": "general",
    "include_answer": true,
    "min_score": 0.5
}'
```

### Response

```json
{
    "job_id": "job_1779392104064657200TsJh",
    "status": "success",
    "status_code": 200,
    "result": {
        "markdown": "...",
        "urls": [
            "https://example.com"
        ]
    },
    "time": {
        "start": "2026-05-21 16:35:04",
        "end": "2026-05-21 16:35:11",
        "duration_seconds": 7.0
    }
}
```

## 4. Document Parse - */parse-content/document-parse*

Recebe um arquivo e um schema JSON para extrair e estruturar seu conteúdo via LLM. Use quando precisar transformar documentos não estruturados (PDFs, Word, texto) em dados organizados e prontos para consumo.

### Parâmetros

| Parâmetro | Tipo | Descrição | Exemplo |
|---|---|---|---|
| `job_id` | `string` | Identificador único do job de parsing, definido pelo cliente. | `"job_contrato_042"` |
| `metadata` | `string` (JSON) | Metadados auxiliares do documento, livres para uso do cliente. | `{"client": "Acme", "doc_type": "contract"}` |
| `document_schema` | `string` (JSON) | Schema que define os campos a extrair. Cada chave recebe `type` e `description`. | `{"summary": {"type": "str", "description": "Resumo do documento"}}` |
| `file` | `file` (upload) | Arquivo a ser processado. Formatos aceitos: `txt`, `md`, `pdf`, `docx`. Limite: 50MB. | `contrato.pdf` |
| `config` | `string` (JSON) — opcional | Configurações do parser: modelo LLM, instruções customizadas e modo debug. | `{"model_provider": "OpenAI", "model_id": "gpt-4.1-mini", "debug_mode": false}` |

### Request

```bash
curl --location 'http://localhost:8000/parse-content/document-parse' \
--header 'X-API-Key: betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0' \
--form 'job_id="teste"' \
--form 'metadata="{\"value1\": \"value3\"}"' \
--form 'document_schema="{
  \"summary\": {
    \"type\": \"str\",
    \"description\": \"Resumo do conteúdo do arquivo\"
  }
}"' \
--form 'config="{
  \"model_provider\": \"OpenAI\",
  \"model_id\": \"gpt-4.1-mini\",
  \"debug_mode\": true,
  \"instructions\": \"Extraia dados do texto\",
  \"description\": \"Leia o texto e extraia as informações relevantes conforme o esquema definido. Retorne um JSON estruturado com os dados extraídos. Caso não encontre alguma informação, retorne null para aquele campo.\"
}"' \
--form 'file=@"/path/to/file"'
```

### Response

```json
{
    "job_id": "job_17793923937296127003HsY",
    "status": "success",
    "status_code": 200,
    "result": {
        "job_id": "teste",
        "content": {
            "job_id": "teste",
            "content": {
                "summary": "..."
            }
        }
    },
    "time": {
        "start": "2026-05-21 16:39:53",
        "end": "2026-05-21 16:40:02",
        "duration_seconds": 9.0
    }
}
```

## 5. Image Generation - */davinci/image-generation*

Gera imagens a partir de um prompt textual, com suporte a instruções de estilo, configurações do modelo e imagens de referência. Use quando precisar criar ou transformar imagens de forma programática via LLM multimodal.

### Parâmetros

| Parâmetro | Tipo | Descrição | Exemplo |
|---|---|---|---|
| `user_input` | `string` | Prompt principal que descreve a imagem a ser gerada. | `"Uma pizzaria napolitana à noite"` |
| `instructions` | `string` — opcional | Instruções adicionais de estilo ou diretrizes criativas para a geração. | `"Estilo de animação 3D como as da Disney"` |
| `config` | `string` (JSON) — opcional | Configurações do modelo: `model`, `temperature`, `top_p`, `max_output_tokens`, `aspect_ratio`, `number_of_images`. | `{"model": "gemini-2.5-flash-image", "aspect_ratio": "9:16"}` |
| `files` | `file[]` — opcional | Imagens de referência para guiar a geração. Aceita múltiplos uploads. | `reference.png` |

### Request

```bash
curl --location 'http://localhost:8000/davinci/image-generation' \
--form 'user_input="Crea l'\''immagine di una pizzeria napoletana"' \
--form 'instructions="Lo stile deve essere un animazione 3d come quelle di disney"' \
--form 'config="{
  \"model\": \"gemini-2.5-flash-image\",
  \"temperature\": 0.75,
  \"top_p\": 0.85,
  \"max_output_tokens\": 1024,
  \"aspect_ratio\": \"9:16\",
  \"number_of_images\": 2
}"' \
--form 'files=@"/path/to/file"'
```

### Response

```json
{
    "status": "success",
    "status_code": 200,
    "result": {
        "model": "gemini-2.5-flash-image",
        "images": [
            {
                "index": 0,
                "base64": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
                "mime_type": "image/png",
                "aspect_ratio": "9:16",
                "resolution": "1080x1920"
            },
            {
                "index": 1,
                "base64": "iVBORw0KGgoAAAANSUhEUgAAAAUB...",
                "mime_type": "image/png",
                "aspect_ratio": "9:16",
                "resolution": "1080x1920"
            }
        ],
        "usage": {
            "prompt_tokens": 312,
            "output_tokens": 1024,
            "total_tokens": 1336
        }
    },
    "time": {
        "start": "2026-05-21 17:45:10",
        "end": "2026-05-21 17:45:23",
        "duration_seconds": 13.2
    }
}
```

---

#### *Author: Enzo Schitini*