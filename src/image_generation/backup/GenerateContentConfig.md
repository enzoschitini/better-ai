## 📄 Guia de Referência: `GenerateContentConfig`

A classe `GenerateContentConfig` permite ajustar desde a "criatividade" do modelo até o formato técnico da resposta. Abaixo, os parâmetros estão divididos por categorias funcionais.

### 1. Amostragem e Criatividade (Randomness)

Estes parâmetros controlam como o modelo escolhe a próxima palavra (token).

* **`temperature`** (`float`): Controla o grau de aleatoriedade. Valores baixos (ex: 0.1) tornam a resposta determinística e objetiva. Valores altos (ex: 0.9) tornam a resposta mais criativa e variada.
* **`top_p`** (`float`): Amostragem por núcleo (nucleus sampling). O modelo escolhe entre os tokens mais prováveis cuja soma de probabilidades atinja este valor.
* **`top_k`** (`float`): Limita a escolha aos `k` tokens mais prováveis em cada etapa.
* **`seed`** (`int`): Define um número para tentar tornar as respostas determinísticas. Se o mesmo seed for usado, o modelo tentará gerar a mesma resposta para o mesmo prompt.

### 2. Instruções e Contexto

* **`system_instruction`** (`ContentUnion`): Define o "personagem" ou regras básicas do modelo. Ex: "Você é um guia turístico especializado em Paris".
* **`cached_content`** (`str`): Nome do recurso de um contexto previamente armazenado em cache para acelerar a resposta e reduzir custos em prompts longos.

### 3. Restrições de Saída

* **`max_output_tokens`** (`int`): O limite máximo de tokens (palavras/caracteres) que o modelo pode gerar.
* **`stop_sequences`** (`list[str]`): Uma lista de strings que, se encontradas, fazem o modelo parar de escrever imediatamente.
* **`candidate_count`** (`int`): Número de variações de resposta que você deseja que o modelo gere para o mesmo prompt.
* **`presence_penalty`** (`float`): Penaliza tokens que já apareceram na resposta, incentivando o modelo a falar sobre novos tópicos.
* **`frequency_penalty`** (`float`): Penaliza tokens que aparecem repetidamente, evitando repetições viciosas de palavras.

### 4. Formatação da Resposta (Estrutura)

* **`response_mime_type`** (`str`): Define o formato do arquivo de saída. Exemplos: `text/plain` (padrão) ou `application/json`.
* **`response_schema`** (`SchemaUnion`): Define uma estrutura (baseada em OpenAPI) para a resposta. Útil para garantir que o modelo retorne um JSON válido com campos específicos.
* **`response_json_schema`** (`Any`): Uma alternativa ao `response_schema` que aceita o padrão [JSON Schema](https://json-schema.org/) completo.
* **`response_modalities`** (`list[str]`): Define que tipos de mídia o modelo pode retornar (ex: texto, áudio, imagem).

### 5. Ferramentas e Funções (Tool Use)

* **`tools`** (`ToolListUnion`): Lista de ferramentas (como funções Python ou busca do Google) que o modelo pode "chamar" para resolver tarefas externas.
* **`tool_config`** (`ToolConfig`): Define como o modelo deve usar as ferramentas (ex: forçar o uso de uma ferramenta específica).
* **`automatic_function_calling`** (`AutomaticFunctionCallingConfig`): Configura se o SDK deve executar as funções sugeridas pelo modelo automaticamente.

### 6. Configurações Avançadas e Multimodais

* **`thinking_config`** (`ThinkingConfig`): Configura recursos de "raciocínio" (Chain of Thought) para problemas complexos.
* **`image_config`** (`ImageConfig`): Parâmetros específicos para quando o modelo gera imagens.
* **`speech_config`** (`SpeechConfigUnion`): Configurações de síntese de voz para respostas em áudio.
* **`audio_timestamp`** (`bool`): Se habilitado, retorna o tempo exato de cada palavra no áudio gerado.
* **`media_resolution`** (`MediaResolution`): Define a qualidade/resolução de mídias processadas ou geradas.

### 7. Segurança e Metadados

* **`safety_settings`** (`list[SafetySetting]`): Filtros para bloquear conteúdo de ódio, assédio, sexualmente explícito ou perigoso.
* **`labels`** (`dict[str, str]`): Etiquetas personalizadas (tags) para organizar custos e faturamento no Google Cloud.

### 8. Diagnóstico e HTTP

* **`response_logprobs`** (`bool`): Se `true`, o modelo retorna a probabilidade logarítmica de cada token escolhido.
* **`logprobs`** (`int`): Quantidade de candidatos a tokens para os quais as probabilidades devem ser retornadas.
* **`http_options`** (`HttpOptions`): Permite sobrescrever configurações da requisição HTTP (como timeouts).
* **`should_return_http_response`** (`bool`): Se `true`, retorna o objeto HTTP bruto junto com a resposta processada.
* **`routing_config`** / **`model_selection_config`**: Configurações internas de roteamento para instâncias específicas do modelo ou versões.

---

### Exemplo Rápido de Uso (Python)

```python
config = GenerateContentConfig(
    temperature=0.7,
    max_output_tokens=500,
    response_mime_type="application/json",
    system_instruction="Responda sempre em português brasileiro de forma amigável.",
    safety_settings=[
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_LOW_AND_ABOVE"}
    ]
)

```
