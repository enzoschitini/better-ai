# BetterAI - cURL

### Start application

```bash
# uvicorn app:app --reload
# http://127.0.0.1:8000
```

### Routers

```bash
origins = [
    "https://better-ai.up.railway.app",
    "https://better-ai-homol.up.railway.app",
    "https://better-ai-dev.up.railway.app",
    "http://127.0.0.1:8000",
]
```

### Headers

```bash
--header 'Authorization: Bearer betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0' \
--header 'Authorization: Bearer betterai-homol-eb8f06ba-faa8-4cfd-b477-1a284b49c494-17422b6c-21f1-4450-9ee5-0505b4854c82' \
--header 'Authorization: Bearer betterai-prod-a65212ba-8ffa-4c35-8fe1-392be1df7a1d-9be169f1-0828-4008-acb9-2bda2d2bd659' \

--header 'Client: BETTERAI' \

--header 'SecretKey: Bearer betterai-dev-6c6febc5-de97-464a-929b-cce1b2278de1' \
--header 'SecretKey: Bearer betterai-homol-b2997bc8-e086-40fd-9e5d-e3d81a03e4be' \
--header 'SecretKey: Bearer betterai-prod-79915d66-2348-4013-9f9f-9200b38efe40' \

--header 'Authorization: Bearer betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0' \
--header 'Client: BETTERAI' \
--header 'SecretKey: Bearer betterai-dev-6c6febc5-de97-464a-929b-cce1b2278de1' \
```

### Vector Store Namespaces

- betterai-embeddings-dev
- betterai-embeddings-homol
- betterai-embeddings-prod

- betterai-embeddings-test-[SCRUM-X]



--------------------------------------------------------------------------------------------------------------------------
## Endpoint health check
--------------------------------------------------------------------------------------------------------------------------

### 1. Healthy - */healthy*

```bash
curl -X GET "http://127.0.0.1:8000/healthy"
```

### 2. Healthy With Authorization - */healthy-authorization*

```bash
curl -X GET "http://127.0.0.1:8000/healthy-authorization" \
--header 'Authorization: Bearer betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0' \
--header 'Client: BETTERAI' \
--header 'SecretKey: Bearer betterai-dev-6c6febc5-de97-464a-929b-cce1b2278de1' \
```


--------------------------------------------------------------------------------------------------------------------------
## Generate ID - */generate-id*
--------------------------------------------------------------------------------------------------------------------------

```bash
curl --location 'http://127.0.0.1:8000/generate-id' \
--header 'Authorization: Bearer betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0' \
--header 'Client: BETTERAI' \
--header 'SecretKey: Bearer betterai-dev-6c6febc5-de97-464a-929b-cce1b2278de1' \
```


--------------------------------------------------------------------------------------------------------------------------
## Chat - */run-agent*
--------------------------------------------------------------------------------------------------------------------------

```bash
curl --location 'http://127.0.0.1:8000/run-agent' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0' \
--header 'Client: BETTERAI' \
--header 'SecretKey: Bearer betterai-dev-6c6febc5-de97-464a-929b-cce1b2278de1' \
--data '{
  "session_id": null,
  "Client": "0011",
  "metadata": {"Client": "1234"},
  "input_text": "Olá",
  "user_prompt": "Você é um agente de IA capaz de analizar uma base de conhecimento...",
  "temperature": 0.5,
  "tool_kit": ["AnswerGeneration"],
  "tool_dic": {
    "AnswerGenerationDic": { "filter_search": { "collection_id": "22" }, "K": 2 }
  },
  "streaming": false
}'
```

- Quais arquivos estão na base?


--------------------------------------------------------------------------------------------------------------------------
## Embeddings
--------------------------------------------------------------------------------------------------------------------------

### Embedding File - */embedding-file*

```bash
curl --location 'http://127.0.0.1:8000/embedding-file' \
--header 'Authorization: Bearer betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0' \
--header 'Client: BETTERAI' \
--header 'SecretKey: Bearer betterai-dev-6c6febc5-de97-464a-929b-cce1b2278de1' \
--form 'payload="{
  \"client_id\": \"0011\",
  \"file_id\": \"21d75dca2eec7b02080327f40220e20dxx2\",
  \"file_url\": \"https://domain.com/docs/21d75dca2eec7b02080327f40220e20dxx2.pdf\",
  \"metadata\": {
    \"filters\": {
      \"collection_id\": \"collection_01\",
      \"Client\": \"1234\",
      \"user_id\": \"11\"
    },
    \"additional_information\": {
      \"collection_name\": \"BetterAI\"
    }
  },
  \"embedding_settings\": {
    \"llm_model\": \"text-embedding-3-large\",
    \"dimensions\": 3072,
    \"global_namespace\": true,
    \"batch_size\": 100
  }
}

"' \
--form 'file=@"/C:/Users/betterai/Downloads/files/example.txt"'
```

### Delete Vectores - */delete-vectors*

```bash
curl -X POST http://127.0.0.1:8000/delete-vectors \
--header 'Authorization: Bearer betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0' \
--header 'Client: BETTERAI' \
--header 'SecretKey: Bearer betterai-dev-6c6febc5-de97-464a-929b-cce1b2278de1' \
  -H "Accept: application/json" \
  -F "target_feature=customer_id" \
  -F "target_id=12345" \
  -F "namespace=clientes"
```

--------------------------------------------------------------------------------------------------------------------------
## Generate Image
--------------------------------------------------------------------------------------------------------------------------

### 1. Generate - */generate-image*

```bash
curl --location 'http://127.0.0.1:8000/generate-image' \
--header 'accept: application/json' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0' \
--header 'Client: BETTERAI' \
--header 'SecretKey: Bearer betterai-dev-6c6febc5-de97-464a-929b-cce1b2278de1' \
--data '{
  "prompt": "Da Vinci style anatomical sketch of a dissected Monarch butterfly. Detailed drawings of the head, wings, and legs on textured parchment with notes in English.",
  "number_of_images": 2,
  "aspect_ratio": "16:9",
  "image_size": "1K",
  "model": "ULTRA"
}'
```

### Da-Vinci 🍌

```bash
curl --location "http://localhost:8000/davinci/image-generation" \
--header "Authorization: Bearer betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0" \
--header "Client: BETTERAI" \
--header "SecretKey: Bearer betterai-dev-6c6febc5-de97-464a-929b-cce1b2278de1" \
--form "user_input=Crea l'immagine di una pizzeria napoletana" \
--form "instructions=Lo stile deve essere un animazione 3d come quelle di disney" \
--form 'config={
  "model": "gemini-2.5-flash-image",
  "temperature": 0.75,
  "top_p": 0.85,
  "max_output_tokens": 1024,
  "aspect_ratio": "9:16",
  "number_of_images": 2
}' \
--form "files=@C:/Users/schit/Downloads/img_177124504231363320002Vw.jpg"
```

### MAX TOKENS:
#### gemini-2.5-flash-image - 1024, 2048
#### gemini-3-pro-image-preview - 4096, 8192


### 2. Delete

```bash
curl --location --request DELETE 'https://better-ai-bucket-storage-production.up.railway.app/delete-images'
```


--------------------------------------------------------------------------------------------------------------------------
## Parse Content
--------------------------------------------------------------------------------------------------------------------------

### Parse Content - */parse-content*

```bash
curl --location 'http://localhost:8000/parse-content/document-parse' \
--header 'Authorization: Bearer betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0' \
--header 'Client: BETTERAI' \
--header 'SecretKey: Bearer betterai-dev-6c6febc5-de97-464a-929b-cce1b2278de1' \
--form 'job_id="teste"' \
--form 'metadata="{\"value1\": \"value3\"}"' \
--form 'schema="{
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
--form 'file=@"c:\\Users\\schit\\better-ai\\src\\content_parse\\module\\Endurance.pdf"'
```


--------------------------------------------------------------------------------------------------------------------------
## Deep Research
--------------------------------------------------------------------------------------------------------------------------

### Context Builder - */deep-research/context-builder*

```bash
curl --location 'http://127.0.0.1:8000/deep-research/context-builder' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0' \
--header 'Client: BETTERAI' \
--header 'SecretKey: Bearer betterai-dev-6c6febc5-de97-464a-929b-cce1b2278de1' \
--data '{
    "query": "Quais as principais tendências de IA em 2026?",
    "search_depth": "advanced",
    "max_results": 2,
    "topic": "general",
    "include_answer": true,
    "min_score": 0.5
  }'
```






## xxxxxxxx - */xxxxxxxx*

```bash

```

Author: Enzo Schitini

