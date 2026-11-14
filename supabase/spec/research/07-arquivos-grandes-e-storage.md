# Arquivos grandes e Storage — Planejamento da classe de arquivos

> **Material de pesquisa (refinamento técnico).** A visão geral citada aqui como "00" / "visão geral" agora vive em [../spec.md](../spec.md). As "Questões em aberto" deste arquivo estão **consolidadas e resolvidas em [../decisions.md](../decisions.md)**, que prevalece em caso de divergência. Tarefas de implementação: [../tasks.md](../tasks.md).

> Status: **rascunho de planejamento** (nenhum código escrito). Itens marcados como **[PROPOSTA]** são sugestões a validar; decisões pendentes estão na seção "Questões em aberto".
> Complementa [spec.md](../spec.md) (seções 3.1 a 3.3 e 4.2) e [01-variaveis-de-ambiente.md](01-variaveis-de-ambiente.md). Vale para a **classe de arquivos** (nome provisório `SupabaseStorage`), uma das três classes da integração; a integradora apenas delega.

## 1. Contexto e objetivo

A frente B (arquivos) precisa tratar qualquer mídia, inclusive **vídeo e áudio grandes**. O risco principal é carregar o arquivo inteiro em memória (upload ou download), travar o processo do backend ou perder um upload longo por falha de rede.

Objetivos desta especificação:

- Subir e baixar arquivos grandes com **memória limitada e previsível** (streaming/chunks).
- Falhar **cedo e com mensagem clara** (tamanho e tipo validados antes de enviar).
- Ter política **determinística** de nomes, caminhos e colisões.
- Expor um contrato **agnóstico ao SDK** (o adapter esconde `supabase-py`, REST ou TUS).

## 2. Fatos da documentação oficial (conferir antes de implementar)

Consultados em 2026-11-14; limites e nomes mudam, então reconfirmar no momento da implementação.

| Tema | O que a documentação diz |
|---|---|
| Limite global | Definido em *Storage Settings* e vale para todos os buckets. Free: até 50 MB. Pro e Team: até 500 GB. Enterprise: sob contrato. |
| Limite por bucket | Pode ser definido por bucket, **sempre menor ou igual ao global**. O bucket também pode restringir tipos MIME permitidos. |
| Upload padrão | Recomendado até ~6 MB. Tecnicamente aceita até 5 GB, mas acima de 6 MB a recomendação é usar resumable. |
| Upload resumable (TUS) | Protocolo TUS. Endpoint `https://<project-id>.storage.supabase.co/storage/v1/upload/resumable` (hostname direto de storage recomendado por performance). **Chunk fixo de 6 MB**. URL de upload válida por até **24 h**. Metadados: `bucketName`, `objectName`, `contentType`, `cacheControl`, `metadata` (JSON em `user_metadata`). Cliente Python citado: `tus-py-client`. |
| Concorrência no TUS | Dois clientes na mesma URL de upload: um falha com `409`. Mesmo caminho com URLs diferentes: o primeiro a terminar vence e o outro recebe `409`; com `x-upsert`, vence o último. |
| Colisão / upsert | Por padrão, gravar em caminho existente retorna `400 Asset Already Exists`. `upsert: true` (ou header `x-upsert: true`) sobrescreve, mas a documentação **desaconselha**: o CDN pode servir conteúdo antigo; preferir **caminho novo**. |
| Content-Type | Inferido pela extensão por padrão; pode ser definido explicitamente (`contentType`). |
| Bucket público | URL pública `.../storage/v1/object/public/<bucket>/<path>`; parâmetro `?download[=nome]` força download. |
| Bucket privado | URL assinada com expiração em segundos; **não é possível revogar uma URL individual** (apagar/mover/renomear o objeto a invalida; revogar todas exige rotacionar a chave de assinatura do projeto). Download autenticado via `.../object/authenticated/...` com header de autorização. |
| Upload por URL assinada | `createSignedUploadUrl` gera token usado no upload (inclusive resumable via `x-signature`). |
| Listagem | Opções `limit`, `offset`, `sortBy` (`column`, `order`) e `search`. A página consultada não declara o `limit` padrão. |

Pontos que a documentação consultada **não deixou claros** (validar com teste real): tamanho máximo do TUS (a doc não declara; presume-se o limite global/bucket), `cache-control` no upload padrão, e limite de itens em remoção em lote.

## 3. Estratégia de transferência

### 3.1 Escolha automática do modo de upload **[PROPOSTA]**

A classe decide o modo pelo tamanho (conhecido antes de enviar, via `stat` do arquivo ou `Content-Length`):

| Tamanho | Modo | Observação |
|---|---|---|
| até 6 MB | Upload padrão | Uma requisição; pode usar bytes em memória sem problema. |
| acima de 6 MB | Resumable (TUS) | Chunks de 6 MB lidos do disco/stream; um chunk em memória por vez. |

O limiar (6 MB) é **configurável** (variável de ambiente ou parâmetro da factory), pois acompanha a recomendação oficial. O chamador pode forçar o modo.

### 3.2 Origem dos dados sem carregar tudo em memória

A entrada do upload aceita **três formas**, nesta ordem de preferência para arquivos grandes:

1. **Caminho local** (`Path`): o adapter abre o arquivo e lê em chunks.
2. **Stream binário** (objeto file-like com `read(n)`): consumido por chunks; não exige `seek` quando o tamanho é informado.
3. **Bytes**: permitido, mas o contrato **recusa bytes acima de um teto** (ex.: 32 MB, configurável) com erro orientando a usar caminho/stream. **[PROPOSTA]**

Regras de memória: o pico de memória por transferência deve ser aproximadamente **1 chunk (6 MB) mais overhead**, independentemente do tamanho do arquivo. Nunca chamar `read()` sem tamanho em arquivos grandes, nem montar o arquivo todo para calcular hash (usar hash incremental, se necessário).

### 3.3 Retomada e falhas

- Falha de rede no meio do upload: o adapter **retoma** a partir do último offset confirmado (função do TUS), com **tentativas limitadas e espera crescente** (ex.: 3 a 5 tentativas). **[PROPOSTA]**
- A URL de upload vale 24 h; passado esse prazo, o upload recomeça do zero (novo upload). O contrato documenta isso.
- Upload interrompido de forma definitiva não deve deixar objeto "meio gravado" visível: confirmar no final (ver critérios de aceite).
- Concorrência no mesmo caminho: tratar `409` como erro de domínio (colisão), não como falha genérica.

### 3.4 Download sem memória

- **Para arquivo:** gravar em disco por chunks (stream HTTP com iteração em blocos de, por exemplo, 1 MB), escrevendo primeiro num arquivo temporário e renomeando ao final (evita arquivo parcial com nome final). **[PROPOSTA]**
- **Como stream:** devolver um iterador/objeto file-like para o chamador consumir (ex.: repassar a uma resposta HTTP do backend).
- **Como bytes:** apenas para arquivos pequenos; o método consulta o tamanho (metadados/`Content-Length`) e **recusa acima do teto** configurado.
- Quando o chamador só precisa que o cliente final baixe, preferir **URL pública ou assinada**, que tira o tráfego do backend.
- Suporte a `Range` (download parcial/retomável) é desejável para vídeo e áudio; fica como **[PROPOSTA]** opcional, pois nem todo SDK expõe.

## 4. Limites de tamanho e validação prévia

Ordem de verificação **antes de abrir conexão** (falha cedo, sem gastar banda):

1. **Teto do projeto na configuração** (`max_file_size_bytes`, valor da própria integração; deve ser menor ou igual ao limite global do plano).
2. **Teto do bucket** (configuração por bucket na integração, espelhando o que está no Supabase).
3. Se o tamanho for desconhecido (stream sem `Content-Length`): contar bytes durante o envio e **abortar ao ultrapassar** o teto.

Como o limite real mora na plataforma, a integração **não deve assumir** os valores: **[PROPOSTA]** manter um mapa de configuração por bucket (`max_size`, `allowed_mime_types`) preenchido pelo usuário/ambiente, e tratar a resposta de erro do Supabase (limite excedido) como `FileTooLargeError`, mesmo quando a validação local não detectar.

Erros de domínio sugeridos: `FileTooLargeError`, `MimeTypeNotAllowedError`, `FileAlreadyExistsError`, `FileNotFoundError` (do domínio, não o builtin), `InvalidPathError`, `StorageTransferError`.

## 5. Validação de tipo

Três camadas, da mais barata à mais confiável:

1. **Extensão** do nome: comparar com lista permitida do bucket (rápido, mas falsificável).
2. **MIME declarado** pelo chamador (`content_type`): comparar com `allowed_mime_types` do bucket (aceitar curingas como `video/*`).
3. **Detecção por conteúdo** (magic bytes): ler somente os **primeiros bytes** (ex.: 2 a 8 KB) do arquivo/stream para identificar o tipo real, sem carregar o resto. **[PROPOSTA]** Biblioteca candidata: `filetype` (puro Python) ou `python-magic` (depende de libmagic, mais pesado no Windows). Decidir na implementação.

Regras:

- Se extensão, MIME declarado e MIME detectado **divergem**, a política padrão é **recusar** (`MimeTypeNotAllowedError` com os três valores na mensagem). Modo permissivo (apenas avisar no log) opcional por configuração. **[PROPOSTA]**
- Quando o MIME não é informado, o contrato usa o **detectado**; na falta, o inferido pela extensão; por último `application/octet-stream`.
- Em stream não "rebobinável", a leitura dos primeiros bytes deve ser **devolvida ao stream** (buffer de reenvio) para o upload não perder esse trecho.
- A mesma lista de tipos permitidos deve estar **também no bucket** (defesa em profundidade): a validação local dá erro claro; a do bucket é a barreira final.

## 6. Política de nomes e caminhos **[PROPOSTA]**

### 6.1 Estrutura de pastas

```
<bucket>/<dominio>/<yyyy>/<mm>/<id-unico>/<nome-sanitizado>.<ext>
ex.: media/videos/2026/11/3f9c.../aula-01.mp4
```

- O **bucket** separa por finalidade e visibilidade (público x privado), não por usuário.
- O primeiro nível dentro do bucket é o **domínio/tipo de uso** (`videos`, `audios`, `documentos`), o que facilita listagem e política de retenção.
- Particionar por data (`yyyy/mm`) evita pastas com milhares de itens (a listagem é paginada por pasta).
- A pasta `<id-unico>` (UUID v4 ou v7) garante unicidade e mantém o **nome original legível** no final do caminho.
- Se o negócio precisar de pasta por entidade (ex.: por usuário ou projeto), inserir `<owner_id>/` após o domínio. Decisão em aberto (Q4).

### 6.2 Sanitização do nome

- Normalizar Unicode (NFKD), remover acentos, converter espaços em `-`, manter apenas `[a-z0-9._-]`, minúsculas, colapsar repetições.
- Rejeitar ou remover: `..`, `/`, `\`, caracteres de controle, nomes que começam com ponto, nomes só de pontos, caracteres reservados do Windows.
- Limitar comprimento do nome (ex.: 100 caracteres) e do caminho completo (a documentação do Storage fixa um limite de chave; conferir na implementação).
- Preservar a extensão original (em minúsculas), validada pela etapa de tipo.
- O **nome original** (como veio do usuário) vai para os **metadados** (`original_name`), não para o caminho.
- Qualquer caminho vindo do chamador passa pelo mesmo validador (`InvalidPathError`), evitando *path traversal* e chaves inesperadas.

### 6.3 Modos de nomeação (strategy injetável)

| Estratégia | Resultado | Uso |
|---|---|---|
| `uuid_folder` (padrão) | `dominio/yyyy/mm/<uuid>/<nome>` | Uploads de usuários/mídia; nunca colide. |
| `uuid_name` | `dominio/<uuid>.<ext>` | Quando o nome original não importa. |
| `explicit` | Caminho informado pelo chamador (validado) | Arquivos com chave de negócio fixa (ex.: `avatar/<user_id>.png`). |
| `content_hash` | `dominio/<sha256>.<ext>` | Deduplicação (exige hash incremental; custo de ler o arquivo uma vez). |

A estratégia é um objeto injetado (Strategy), mantendo aberto/fechado: novas políticas entram sem alterar a classe.

## 7. Colisão de nomes

Opções e comportamento no Supabase:

| Política | Como | Prós | Contras |
|---|---|---|---|
| **Recusar** (padrão do Supabase, `400 Asset Already Exists`) | Sem `upsert` | Seguro, sem perda de dados. | Exige o chamador tratar o conflito. |
| **Sobrescrever** | `upsert: true` / `x-upsert` | Simples para chaves fixas. | **Doc oficial desaconselha**: CDN pode servir versão antiga; perde o conteúdo anterior. |
| **Versionar** | Novo caminho por versão (ex.: `.../v2/`, sufixo, ou UUID novo) | Sem cache obsoleto; histórico. | Mais objetos; precisa de ponteiro "atual" (normalmente numa tabela). |

**Recomendação [PROPOSTA]:**

- Padrão da classe: **`on_conflict = "reject"`**, com `FileAlreadyExistsError`.
- Com a estratégia `uuid_folder`, colisão praticamente não ocorre; o problema só aparece em `explicit`.
- Para "substituir" um arquivo lógico (ex.: foto de perfil), **versionar**: gravar em caminho novo e atualizar a referência na tabela; apagar o antigo depois (limpeza). Isso evita o problema de cache do CDN.
- `overwrite` (upsert) disponível, mas **explícito e registrado em log como aviso**; recomendado só para objetos privados que não passam por CDN ou quando stale cache é aceitável.
- Parâmetro do contrato: `on_conflict: reject | overwrite | version`. No modo `version`, a classe devolve o caminho final usado.

## 8. Metadados e content-type

- **Content-Type:** definido explicitamente pela cadeia da seção 5 (nunca depender só da inferência do servidor, principalmente em vídeo/áudio, para o navegador reproduzir corretamente).
- **cache-control:** parâmetro opcional com padrão conservador por tipo (**[PROPOSTA]**: privado `no-cache`/curto; mídia imutável em caminho com UUID pode usar cache longo, já que o caminho nunca é reutilizado).
- **Metadados customizados:** dicionário de string para string (no TUS vai em `metadata`, armazenado em `user_metadata`). Sugestão de chaves padrão: `original_name`, `uploaded_by`, `source`, `sha256` (opcional), `duration_s` (opcional, se o backend souber). Não gravar dados sensíveis.
- **Resultado do upload** devolve um objeto descritivo (ver seção 12) com bucket, caminho, tamanho, content-type e metadados efetivos.
- Consulta de metadados sem baixar o arquivo (`info`/`exists`): tamanho, content-type, datas, metadados.

## 9. Formas de recuperação

| Forma | Quando usar | Memória | Observações |
|---|---|---|---|
| **Bytes** | Arquivos pequenos (config, thumbnails) | Arquivo inteiro | Recusa acima do teto. |
| **Stream** | Repassar ao cliente HTTP, processar em fluxo | 1 chunk | O chamador deve fechar o stream (context manager). |
| **Para arquivo (disco)** | Processamento posterior (ex.: transcodificar vídeo) | 1 chunk | Escrita atômica via arquivo temporário. |
| **URL pública** | Bucket público, conteúdo aberto | Nenhuma no backend | Só funciona em bucket público; aceita `download=<nome>`. |
| **URL assinada** | Bucket privado, acesso temporário ao cliente final | Nenhuma no backend | Expiração obrigatória; **não revogável individualmente**. |

Regras:

- O contrato **conhece a visibilidade do bucket** (configuração) e **recusa** pedir URL pública de bucket privado (`BucketAccessError`), em vez de devolver link quebrado.
- Expiração padrão da URL assinada configurável (ex.: 1 h) e com **teto** (ex.: 24 h). Para vídeo longo, o tempo precisa cobrir a reprodução inteira. **[PROPOSTA]**
- **Upload direto pelo cliente final** (backend só emite a URL de upload assinada) fica como **[PROPOSTA]** opcional: tira arquivos enormes do backend por completo. Entra no contrato como `create_signed_upload_url`, mas depende da decisão Q6.
- URLs assinadas nunca são gravadas em log completas (o token é segredo): registrar só bucket, caminho e expiração.

## 10. Listagem e paginação

- O contrato lista **por prefixo (pasta)**, não por bucket inteiro: `list(bucket, prefix, limit, offset, sort, search)`.
- Paginação por `limit`/`offset` (o que o Storage oferece), ordenação por coluna (`name`, `created_at`, `updated_at`) e direção.
- **Tamanho de página padrão** definido pela integração (ex.: 100), com teto (ex.: 1000), pois a documentação consultada não declara o padrão do servidor.
- Devolver também um indicador de "há mais" (página retornou `limit` itens). Para varrer tudo, oferecer um **iterador** que busca página a página (sem acumular a lista inteira em memória). **[PROPOSTA]**
- Listagem retorna **pastas e arquivos**; o objeto de resultado diferencia os dois.
- Não é recursiva por padrão; busca recursiva (percorrer subpastas) é opcional e deve ter limite de profundidade.
- Atenção: `search` filtra por nome, não por conteúdo.

## 11. Exclusão

- **Um arquivo:** `delete(bucket, path)`. Comportamento sobre inexistente: **idempotente por padrão** (não é erro apagar o que já não existe), com flag `strict=True` para lançar `FileNotFoundError`. **[PROPOSTA]**
- **Lote:** `delete_many(bucket, paths)`, aceitando uma lista; o adapter **divide em lotes** (tamanho configurável, ex.: 100) caso a API tenha limite.
- O resultado do lote informa **o que foi removido e o que falhou** (sem abortar tudo no primeiro erro), com motivo por item.
- **Pasta:** o Storage não tem pasta real; "apagar pasta" = listar por prefixo (paginado) e apagar em lote. Operação **destrutiva**: exige parâmetro explícito (`confirm_prefix`) e log de aviso. **[PROPOSTA]**
- Apagar invalida URLs assinadas do objeto (comportamento documentado).
- Ao versionar (seção 7), a limpeza de versões antigas usa o mesmo lote.

## 12. Contrato da classe de arquivos (pseudo-assinaturas, agnóstico ao SDK)

Apenas tipos do domínio entram e saem; nada do SDK vaza. Nomes provisórios.

```
Tipos de apoio
  FileRef            : bucket, path
  StoredFile         : bucket, path, size_bytes, content_type, metadata, created_at, etag/versão (se houver)
  UploadSource       : caminho local | stream binário | bytes (+ tamanho opcional)
  ListPage           : itens (arquivos e pastas), tem_mais, próximo_offset
  DeleteReport       : removidos[], falhas[(path, motivo)]
  ProgressCallback   : (bytes_enviados, total|None) -> None

Contrato FileStorage (interface)
  upload(bucket, source, *, path=None, name=None, content_type=None,
         metadata=None, cache_control=None, on_conflict="reject",
         mode="auto", progress=None) -> StoredFile
  download_bytes(ref, *, max_bytes=None) -> bytes
  download_stream(ref, *, chunk_size=None) -> iterador/stream binário (fecha com context manager)
  download_to_file(ref, destino, *, chunk_size=None, overwrite=False) -> caminho final
  info(ref) -> StoredFile
  exists(ref) -> bool
  public_url(ref, *, download_as=None) -> str
  signed_url(ref, *, expires_in=None, download_as=None) -> str
  create_signed_upload_url(bucket, path, *, expires_in=None) -> (url, token)      [PROPOSTA, opcional]
  list(bucket, prefix="", *, limit=None, offset=0, sort_by="name", order="asc", search=None) -> ListPage
  iter_list(bucket, prefix="", *, page_size=None, ...) -> iterador de itens
  delete(ref, *, strict=False) -> bool
  delete_many(bucket, paths, *, batch_size=None) -> DeleteReport
  delete_prefix(bucket, prefix, *, confirm_prefix) -> DeleteReport                 [PROPOSTA]

Dependências injetadas na construção (DI)
  adapter de transporte (fala com o Supabase: padrão e resumable)
  validador (tamanho + tipo)         estratégia de nomeação / sanitizador
  configuração por bucket (visibilidade, max_size, tipos permitidos)
  logger (contrato próprio)          relógio/gerador de UUID (para testes)
```

Observações de design:

- **Interface segregada (I):** separar mentalmente leitura, escrita e URLs; se crescer, dividir em `FileWriter`, `FileReader`, `FileUrlProvider`, mantendo a classe de arquivos como composição.
- **Adapter:** duas implementações de transporte atrás do mesmo contrato interno: `StandardUploader` (≤ 6 MB) e `ResumableUploader` (TUS). A classe escolhe por tamanho (seção 3.1). Trocar de SDK mexe só aqui.
- **Factory:** monta a classe com a configuração (limiar, tetos, buckets, estratégia de nomes) e entrega pronta à integradora.
- **Logs** (seção 3.2 da visão geral): registrar operação, bucket, caminho, tamanho, modo (padrão/TUS), duração, tentativas e resultado; níveis e cores conforme o padrão. Em `DEBUG`, progresso por chunk. **Nunca** conteúdo do arquivo, tokens, chaves nem URL assinada completa.
- **Sem estado oculto:** a classe não guarda arquivo em memória nem cache de bytes.

## 13. Síncrono x assíncrono em arquivos grandes

- Chamadas síncronas bloqueiam a thread durante todo o upload/download. Em um servidor FastAPI, isso **bloqueia o event loop** se for chamado dentro de `async def`, travando outras requisições.
- Opções:
  1. **Contrato síncrono + execução em thread/pool** (ex.: o chamador usa `run_in_threadpool`/`asyncio.to_thread`). Simples; o SDK `supabase-py` oferece cliente síncrono e assíncrono, e `tus-py-client` é síncrono.
  2. **Contrato assíncrono nativo**: melhor encaixe com FastAPI, porém o TUS em Python é síncrono, exigindo thread de qualquer forma.
- **Recomendação [PROPOSTA]:** definir o contrato em **duas variantes finas com os mesmos nomes** (síncrona e assíncrona), ou só a síncrona com wrapper assíncrono baseado em thread. Para arquivos grandes, **nunca** executar transferência síncrona direto no event loop. Decisão final vinculada à questão 2 da visão geral.
- Em qualquer variante: **timeouts** explícitos (conexão e leitura) compatíveis com chunks de 6 MB; possibilidade de **cancelamento** (parar e limpar temporários); limite de **transferências simultâneas** (semáforo) para não estourar memória/banda (ex.: máximo de N × 6 MB em memória).
- Barras de progresso/callbacks devem ser leves, pois rodam no caminho quente do chunk.

## 14. Exemplos de cenários

1. **Vídeo de 800 MB (do disco):** `upload(bucket="media", source=<caminho>, name="Aula 01.mp4")`. A classe sanitiza o nome, valida tamanho (≤ teto do bucket) e tipo (magic bytes = `video/mp4`), escolhe TUS, envia em chunks de 6 MB com retomada e devolve `StoredFile` com o caminho `videos/2026/11/<uuid>/aula-01.mp4`. Pico de memória ≈ 6 MB.
2. **Áudio chegando como stream de uma requisição HTTP:** sem tamanho conhecido; a classe lê os primeiros bytes para detectar o tipo, conta bytes ao enviar e aborta se passar do teto, devolvendo `FileTooLargeError`.
3. **Arquivo com extensão `.mp3` que na verdade é um executável:** detecção por conteúdo diverge da extensão; recusa com `MimeTypeNotAllowedError`.
4. **Substituir a foto de perfil:** modo `version`: grava novo caminho, o backend atualiza a tabela e chama `delete` no antigo. Sem problema de cache do CDN.
5. **Entregar vídeo privado ao cliente:** `signed_url(ref, expires_in=7200)`; o backend não trafega os bytes.
6. **Baixar um vídeo para transcodificar:** `download_to_file(ref, destino)`; grava em temporário e renomeia ao concluir.
7. **Limpar uma pasta de 5.000 objetos:** `delete_prefix(..., confirm_prefix="videos/2026/10/")`; lista paginando, apaga em lotes e devolve `DeleteReport`.
8. **Queda de rede aos 70%:** o upload retoma do último offset; se a URL de upload passou de 24 h, recomeça e registra aviso no log.

## 15. Critérios de aceite

- Upload de arquivo de **pelo menos 1 GB** (ou do maior permitido pelo plano usado no teste) mantém o pico de memória do processo **abaixo de um valor definido** (ex.: 64 MB acima da linha de base), medido em teste.
- Download para arquivo e como stream de arquivo grande mantém memória estável; `download_bytes` acima do teto é **recusado** sem baixar nada.
- Arquivo acima do limite (projeto ou bucket) é recusado **antes de qualquer requisição** quando o tamanho é conhecido; em stream, é abortado ao exceder.
- Tipo divergente (extensão x MIME x conteúdo) é recusado com mensagem que mostra os três valores.
- Nomes com acentos, espaços, `..`, `/`, caracteres de controle e nomes longos resultam em caminho seguro ou em `InvalidPathError`; nenhum caminho sai do prefixo esperado.
- Colisão com política `reject` gera `FileAlreadyExistsError`; `overwrite` sobrescreve e registra aviso; `version` devolve novo caminho e preserva o antigo.
- Upload interrompido é retomado sem reenviar chunks já confirmados; após falha definitiva não resta objeto parcial visível.
- Content-Type e metadados gravados são lidos de volta idênticos via `info`.
- URL pública de bucket privado é recusada; URL assinada respeita expiração e teto; logs não contêm a URL assinada completa.
- Listagem paginada percorre mais de uma página sem duplicar nem pular itens; `iter_list` não acumula tudo em memória.
- `delete` é idempotente (e estrito quando pedido); `delete_many` reporta sucesso e falha por item; `delete_prefix` exige confirmação.
- Chamada dentro de um contexto assíncrono não bloqueia o event loop (teste com outra tarefa rodando em paralelo).
- Nenhuma exceção do SDK vaza: tudo vira erro de domínio. A classe funciona com um **adapter falso** em testes, sem rede.
- Logs: nível configurável, cores por nível, nenhum segredo ou conteúdo de arquivo.

## 16. Questões em aberto

1. **Plano do Supabase e limite global real** (Free 50 MB x Pro até 500 GB). *Recomendação:* informar o plano e configurar os tetos da integração com valores iguais ou menores que os da plataforma; testes de arquivo grande só fazem sentido com limite adequado.
2. **Síncrono ou assíncrono** (herda a Q2 da visão geral). *Recomendação:* contrato síncrono com adapter thread-safe e wrapper assíncrono por thread, já que o TUS Python é síncrono.
3. **Buckets e visibilidade** (herda Q5): quais existem, públicos ou privados, e quais tipos/tamanhos cada um permite? *Recomendação:* um bucket privado para mídia de usuário e outro público só para ativos estáticos.
4. **Pasta por dono/entidade?** O caminho deve incluir `<owner_id>`? *Recomendação:* sim, se houver necessidade de apagar tudo de um usuário ou de políticas de acesso por pasta; do contrário, manter só domínio + data + UUID.
5. **Política de colisão padrão.** *Recomendação:* `reject`, com `version` para substituições lógicas e `overwrite` só por escolha explícita.
6. **Upload direto do cliente final por URL assinada** entra no escopo? *Recomendação:* deixar como fase posterior; o backend já cobre o caso inicial.
7. **Biblioteca de detecção de tipo** (`filetype` x `python-magic`). *Recomendação:* `filetype` por não depender de libmagic no Windows; cobre os formatos comuns de vídeo, áudio, imagem e PDF.
8. **Teto para bytes em memória** e **tamanho de página/lote** padrão. *Recomendação:* 32 MB, página 100, lote de exclusão 100; ajustar após teste real.
9. **Estratégia de limpeza** de objetos órfãos (upload concluído sem registro na tabela) e retenção. *Recomendação:* rotina futura que compara tabela x bucket; fora desta fase.
10. **Tamanho máximo efetivo do TUS** e limite de itens por remoção em lote: a documentação consultada não declara. *Recomendação:* validar por teste real antes de fixar valores.

## 17. Referências

URLs consultadas (2026-11-14):

- Limites de arquivo: <https://supabase.com/docs/guides/storage/uploads/file-limits>
- Uploads resumable (TUS): <https://supabase.com/docs/guides/storage/uploads/resumable-uploads>
- Uploads padrão: <https://supabase.com/docs/guides/storage/uploads/standard-uploads>
- Download e entrega de arquivos (URL pública/assinada): <https://supabase.com/docs/guides/storage/serving/downloads>
- Referência Python, listagem: <https://supabase.com/docs/reference/python/storage-from-list>
- Base do projeto: [spec.md](../spec.md), [01-variaveis-de-ambiente.md](01-variaveis-de-ambiente.md)
