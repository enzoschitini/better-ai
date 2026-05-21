# Web Service Network - API

...blablabla...

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
        "markdown": "## Research Context\n\n### Answer\nAs principais tendências de IA em 2026 incluem agentes autônomos, modelos multimodais e IA embarcada em dispositivos de borda. Empresas como Google, OpenAI e Anthropic lideram o desenvolvimento de sistemas capazes de raciocinar em múltiplas etapas sem intervenção humana.\n\n---\n\n### Sources\n\n#### 1. The Top AI Trends Shaping 2026\n**URL:** https://techcrunch.com/2026/ai-trends\n**Score:** 0.94\n\nAgents are increasingly replacing traditional pipelines. Companies like Microsoft and Salesforce have embedded autonomous agents directly into their core products...\n\n#### 2. Multimodal AI: The Next Frontier\n**URL:** https://research.google/blog/multimodal-2026\n**Score:** 0.89\n\nWith the rise of vision-language models, enterprises are adopting multimodal AI to process documents, images and audio in unified pipelines...\n\n#### 3. Edge AI and On-Device Intelligence\n**URL:** https://www.wired.com/story/edge-ai-2026\n**Score:** 0.81\n\nSmartphones and IoT devices now run quantized LLMs locally, reducing latency and eliminating dependence on cloud infrastructure...",
        "urls": [
            "https://techcrunch.com/2026/ai-trends",
            "https://research.google/blog/multimodal-2026",
            "https://www.wired.com/story/edge-ai-2026"
        ]
    },
    "time": {
        "start": "2026-05-21 16:35:04",
        "end": "2026-05-21 16:35:11",
        "duration_seconds": 7.0
    }
}
```

---

#### *Author: Enzo Schitini*




Você é um especialista em documentação técnica de APIs REST.

Dado o código de um endpoint e seu curl de exemplo, gere uma documentação clara e objetiva no seguinte formato:

---

## {N}. {Nome do Endpoint} - *{/rota/completa}*

Um parágrafo descrevendo o que o endpoint faz, para que serve e quando usá-lo.

### Parâmetros

Tabela com as colunas: Parâmetro | Tipo | Descrição | Exemplo

### Request

Bloco curl pronto para execução, com o header X-API-Key como `******`.

### Response

Bloco JSON realista simulando um retorno de sucesso, com dados coerentes ao contexto da query usada no curl.

---

**Regras:**
- O número `{N}` deve ser fornecido por mim junto com o código
- A descrição do endpoint deve ser em 1–2 frases diretas, sem enrolação
- Os tipos dos parâmetros devem refletir exatamente o que está no código (ex: `"basic" | "advanced"`, `float (0.0–1.0)`)
- O JSON de response deve ser realista: simule dados que fariam sentido para a query do curl
- Escreva em português, mas mantenha nomes de parâmetros, rotas e tipos em inglês
- Não adicione seções extras além das especificadas