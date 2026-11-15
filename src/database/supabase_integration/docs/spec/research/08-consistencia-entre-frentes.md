# Consistência entre as frentes (tabelas x arquivos)

> **Material de pesquisa (refinamento técnico).** A visão geral citada aqui como "00" / "visão geral" agora vive em [../spec.md](../spec.md). As "Questões em aberto" deste arquivo estão **consolidadas e resolvidas em [../decisions.md](../decisions.md)**, que prevalece em caso de divergência. Tarefas de implementação: [../tasks.md](../tasks.md).

> Status: **rascunho de planejamento** (nenhum código escrito). Itens marcados como **[PROPOSTA]** são sugestões a validar; decisões que dependem do usuário estão em **Questões em aberto** (seção 12), cada uma com recomendação.
> Complementa [spec.md](../spec.md) e [01-variaveis-de-ambiente.md](01-variaveis-de-ambiente.md).

## 1. Contexto e problema

A integração tem duas frentes independentes (ver 00, seção 3.1): a classe de **tabelas** (Postgres via API) e a classe de **arquivos** (Storage). Muito provavelmente, um registro de tabela vai **referenciar** um arquivo (ex.: coluna com `bucket` + `path` do objeto). O fluxo típico do backend é "salvar arquivo + salvar registro que aponta para ele", ou o inverso para apagar.

O problema: **Postgres e Storage são sistemas separados e não existe transação que cubra os dois.** O Storage guarda os bytes em armazenamento de objetos; seus metadados também aparecem em tabelas do schema `storage`, mas isso é detalhe interno do Supabase, e a integração não deve depender dele nem escrever ali. Cada chamada (insert, upload, delete) é independente, pode falhar sozinha e não tem rollback automático.

Consequência: qualquer operação composta pode terminar em estado **parcial** se algo falhar no meio (rede, timeout, política, cota, processo morto).

## 2. Cenários de falha

| # | Cenário | Resultado | Gravidade |
|---|---|---|---|
| F1 | Upload ok, insert falha | **Arquivo órfão** no bucket (ocupa espaço, ninguém aponta para ele) | Média (custo, sujeira) |
| F2 | Insert ok, upload falha | **Registro apontando para nada** (link quebrado para o usuário) | Alta (erro visível) |
| F3 | Delete do registro ok, delete do arquivo falha | Arquivo órfão | Média |
| F4 | Delete do arquivo ok, delete do registro falha | Registro apontando para nada | Alta |
| F5 | Falha de **resposta** (timeout) com a operação já efetivada no servidor | Cliente acha que falhou, mas aconteceu; retry pode duplicar ou conflitar | Alta (ambiguidade) |
| F6 | Processo morre entre os dois passos | Qualquer estado parcial acima, **sem chance de compensar em memória** | Alta |
| F7 | Update de registro trocando o arquivo (novo upload + atualizar referência + apagar o antigo) | Combinação de F1/F3: arquivo novo ou antigo órfão | Média |
| F8 | Arquivo apagado por fora (painel, outro serviço) | Registro aponta para nada | Baixa (fora do nosso controle) |

Regra de ouro para escolher a estratégia: **órfão é aceitável e barato de limpar; link quebrado não é.** Um arquivo sobrando custa espaço; um registro apontando para o vazio quebra o usuário. A ordem das operações deve favorecer o primeiro tipo de erro.

## 3. Opções de projeto

### 3.1 Ordem das operações

- **Gravar:** upload primeiro, insert depois. Se o upload falha, nada foi gravado (limpo). Se o insert falha, sobra um arquivo órfão (F1), que é o erro "barato".
- **Apagar:** apagar o **registro primeiro**, o arquivo depois. Se o segundo passo falha, sobra órfão (F3) em vez de link quebrado (F4).
- **Substituir arquivo:** upload do novo (caminho novo) -> atualizar registro -> apagar o antigo. Falhas deixam órfão, nunca link quebrado.

Prós: custo zero de implementação, elimina a classe de erro mais grave. Contras: não elimina órfãos, só os troca pelo mal menor.

### 3.2 Compensação manual (estilo Saga)

Cada passo composto registra o desfazimento do passo anterior: se o insert falha, tenta apagar o arquivo recém-enviado; se o delete do arquivo falha após apagar o registro, tenta recriar... (este último normalmente não vale a pena; ver recomendação).

Prós: resolve a maioria dos casos no mesmo fluxo, sem infraestrutura nova. Contras: a compensação **também pode falhar**; não cobre morte do processo (F6); mais código e mais caminhos de teste.

### 3.3 Estado pendente/confirmado

O registro nasce com `status = pending`, o arquivo é enviado, e só então o registro vai para `confirmed`. Leituras comuns filtram `confirmed`. Isso converte "link quebrado" em "registro pendente visível a quem limpa".

Prós: torna F2/F6 detectáveis e inofensivos; base para a limpeza. Contras: exige **coluna extra no schema** do usuário (a integração não faz DDL, ver 00 seção 5), obriga as consultas a filtrarem o estado, e acrescenta um segundo write por operação.

### 3.4 Rotina de limpeza de órfãos (reconciliação)

Um processo separado compara o que existe no bucket com o que as tabelas referenciam e apaga (ou apenas reporta) o que sobrou; idem para registros `pending` antigos.

Prós: é a **única** rede de segurança que cobre F6 e F8. Contras: precisa saber quais tabelas/colunas referenciam arquivos (acoplamento de configuração), custo de listar buckets grandes, risco de apagar arquivo "em voo" (upload feito, insert ainda não) se não houver janela de tolerância.

### 3.5 Constraint/trigger no banco

Ex.: trigger que, ao apagar um registro, enfileira o caminho do arquivo numa tabela de "arquivos a apagar".

Prós: garante a intenção de apagar mesmo se o backend morrer. Contras: é DDL/lógica no banco, fora do escopo da integração; não consegue apagar o objeto sozinho (o banco não fala com o Storage de forma transacional); aumenta o acoplamento com o schema. Fica como **evolução futura**.

### 3.6 Deixar fora do escopo da v1

Prós: simplicidade. Contras: sem nenhuma proteção, F1 e F2 acontecerão em produção e ninguém saberá. Não recomendado como única medida.

## 4. Recomendação **[PROPOSTA]**

Para a v1, combinar o barato e eficaz, sem exigir mudança de schema:

1. **Ordem das operações da seção 3.1** como regra fixa da fachada (grava: arquivo -> registro; apaga: registro -> arquivo).
2. **Compensação de melhor esforço (best effort)** apenas nos dois casos simples: insert falhou após upload -> tentar apagar o arquivo; update falhou após novo upload -> tentar apagar o novo. Se a compensação falhar, **não propagar um segundo erro**: registrar um log de nível ERROR estruturado com `bucket`, `path`, `operacao`, `correlation_id` e a marca `orfao_possivel=true`. Esse log é o insumo para limpeza manual.
3. **Resultado explícito:** a fachada devolve ao chamador um resultado que informa se a operação foi `completa`, `parcial` (com o que sobrou) ou `falhou`, em vez de esconder o estado parcial.
4. **Sem estado pendente/confirmado, sem rotina de limpeza e sem trigger na v1.** Ficam como evolução (seção 10). O estado pendente exige coluna no schema do usuário, o que depende de decisão dele (questão 1).
5. **Ferramenta de reconciliação sob demanda** é mantida como evolução, mas o log da etapa 2 já permite a limpeza manual na v1.

Justificativa: a ordem correta elimina o erro grave; a compensação de melhor esforço resolve o caso comum (falha do insert por validação, constraint ou rede); o log deixa os casos raros rastreáveis. É o menor conjunto que dá segurança real sem criar infraestrutura.

## 5. Onde a lógica mora

- A **classe integradora (fachada)** é a única que conhece as duas frentes e, portanto, a **única que orquestra operações compostas** (ordem, compensação, resultado parcial).
- A **classe de tabelas** e a **classe de arquivos** **não se conhecem** e **não sabem** que existe compensação. Cada uma só garante que sua própria operação é atômica no seu sistema e devolve erros de domínio claros.
- **Contrato mínimo exigido das duas** para a compensação funcionar: a classe de arquivos devolve o identificador exato do que gravou (bucket + path) e a classe de tabelas devolve o registro criado com o id. A fachada usa isso para compensar. Nenhuma das duas importa a outra.
- **[PROPOSTA]** A orquestração fica em operações nomeadas da fachada (pseudo-assinaturas):
  - `salvar_registro_com_arquivo(tabela, dados, bucket, destino, conteudo, ...) -> ResultadoComposto`
  - `apagar_registro_com_arquivo(tabela, id, campo_referencia_arquivo, ...) -> ResultadoComposto`
  - `substituir_arquivo_do_registro(tabela, id, bucket, destino, conteudo, ...) -> ResultadoComposto`
- As operações simples (só tabela ou só arquivo) continuam sendo delegação direta, sem orquestração.
- **[PROPOSTA]** Para manter a fachada fina (SOLID), a lógica de passos/compensação pode viver num colaborador interno injetado (ex.: um "coordenador de operações compostas") em vez de dentro da própria fachada. Detalhe a fechar na etapa de arquitetura.
- Como a fachada depende apenas dos contratos (D de SOLID), os testes podem usar fakes das duas frentes que falham em pontos programados e verificar a compensação.

## 6. Relação com erros

- Erros do domínio (ver 00 seção 3): a fachada distingue **falha total** (nada mudou), **falha parcial** (algo ficou para trás) e **falha na compensação**.
- **[PROPOSTA]** Um erro específico de "operação composta parcial" carrega: etapa que falhou, etapas concluídas, se a compensação foi tentada e seu resultado, e as referências (tabela/id, bucket/path) necessárias para limpeza. Nunca carrega conteúdo de arquivo ou valores de registro.
- Exceções do SDK nunca vazam; são traduzidas pelo adapter e a fachada trabalha só com erros do domínio.
- A compensação **nunca mascara o erro original**: o erro que chega ao chamador é o da operação principal, com a informação da compensação anexada.

## 7. Relação com retry

- O retry vale **por operação simples** (dentro da classe de tabelas ou de arquivos), apenas para falhas transitórias (rede, timeout, 5xx), com número máximo e espera crescente configuráveis. **[PROPOSTA]**
- **Não** repetir o fluxo composto inteiro às cegas: isso reexecutaria passos já concluídos. Se for necessário retomar, a fachada reexecuta só a etapa que falhou.
- Falhas definitivas (validação, permissão, arquivo já existe sem upsert, registro não encontrado) **não** são repetidas.
- Atenção a F5 (resposta perdida): antes de repetir um insert ou upload ambíguo, a operação precisa ser idempotente (seção 8), senão o retry cria duplicata ou conflito.

## 8. Idempotência

Objetivo: repetir uma operação (por retry ou por reenvio do cliente) produz o mesmo estado final.

- **Arquivos:** usar **caminho determinístico** definido pelo chamador ou derivado de um id estável (ex.: `<id-do-registro>/<nome>`), em vez de nome aleatório gerado a cada tentativa. Assim o retry do upload reescreve o mesmo objeto. O upload do Storage falha por padrão se o objeto já existe e oferece a opção de *upsert* para sobrescrever; a política escolhida deve ser explícita por operação. **[PROPOSTA]**
- **Registros:** o id do registro deve ser **gerado antes** da primeira tentativa (pelo chamador ou pela fachada) e reutilizado nos retries, de modo que a repetição do insert seja um *upsert* por esse id ou falhe de forma reconhecível por conflito, e não crie duplicata. **[PROPOSTA]**
- **Deletes:** apagar algo que já não existe deve ser tratado como **sucesso** (efeito desejado já alcançado), com log em nível informativo ou debug, não erro. **[PROPOSTA]**
- **Chave de correlação:** cada operação composta recebe um `correlation_id` (gerado se o chamador não passar) que aparece em todos os logs das etapas, ligando upload, insert e compensação. **[PROPOSTA]**

## 9. Relação com logs

Seguindo 00 seção 3.2 (nível configurável, cores, sem segredos):

- Cada etapa de uma operação composta loga início e fim com: `operacao`, `etapa (n/total)`, `tabela` ou `bucket`, `identificador`, `duracao_ms`, `resultado`, `correlation_id`.
- Compensação tem destaque próprio: **aviso (WARNING)** quando a compensação foi necessária e deu certo; **ERROR** quando a compensação falhou, sempre com `orfao_possivel=true` ou `registro_quebrado_possivel=true` e as referências para limpeza.
- Estado final da operação composta (`completa`/`parcial`/`falhou`) é logado em uma única linha de resumo, para facilitar busca.
- Nunca logar conteúdo do arquivo, valores dos campos do registro nem chaves. Caminhos de objeto e ids são permitidos.
- Em `DEBUG`, logar a sequência de passos planejada e a lista de compensações registradas antes de executar.

## 10. Fora de escopo na v1 e evolução futura

**Fora de escopo na v1 (explícito):**

- Garantia transacional real entre Postgres e Storage (não existe; não prometer).
- Rotina automática de limpeza de órfãos agendada.
- Estado pendente/confirmado (exige coluna no schema do usuário; sem DDL na integração).
- Triggers, funções ou filas no banco.
- Recuperação após morte do processo (F6) e detecção de arquivos apagados por fora (F8).
- Operações em lote com garantias entre itens (cada item é independente; lote é "melhor esforço" com relatório por item).
- Versionamento e lixeira de arquivos.

**Evolução futura (registrada):**

1. Estado pendente/confirmado, se o usuário aceitar a coluna extra.
2. Ferramenta de **reconciliação** sob demanda (relatório primeiro, depois remoção), com janela de tolerância para não apagar objetos "em voo".
3. Fila de "arquivos a apagar" alimentada por trigger, com um consumidor que apaga via API de Storage.
4. Registro persistente de operações compostas (um diário de passos) para retomar após queda do processo.
5. Métricas de parciais e compensações.

## 11. Critérios de aceite

1. Existe, na fachada, ao menos as três operações compostas da seção 5, e as classes de tabelas e arquivos **não importam uma à outra** (verificável por inspeção dos imports).
2. Gravar: com o fake de tabelas falhando no insert, o arquivo enviado é apagado via compensação e o chamador recebe o erro original com a informação da compensação.
3. Gravar: com upload falhando, nenhum registro é criado.
4. Apagar: o registro é apagado antes do arquivo; com o delete do arquivo falhando, o resultado é `parcial`, nenhum erro de link quebrado é produzido e há log ERROR com `bucket`, `path` e `orfao_possivel=true`.
5. Substituir: em qualquer falha, o registro nunca fica apontando para um arquivo inexistente.
6. Se a própria compensação falha, o erro original é preservado, nenhum segundo erro é lançado e o log ERROR traz as referências para limpeza manual.
7. Repetir a mesma operação composta com os mesmos parâmetros (mesmo id e caminho) não cria duplicatas nem falha em delete de item já inexistente.
8. Retry atua só em falhas transitórias, com limites configuráveis, e não repete passos já concluídos.
9. Todos os logs de operação composta trazem o mesmo `correlation_id` e uma linha de resumo com o estado final, sem segredos nem conteúdo.
10. Testes com fakes cobrem F1, F2, F3, F4, F5 (resposta perdida simulada) e falha na compensação.
11. A documentação deixa claro ao consumidor que **não há atomicidade** e como interpretar o resultado `parcial`.

## 12. Questões em aberto

| # | Questão | Recomendação |
|---|---|---|
| 1 | Aceita-se adicionar uma coluna de estado (`pending`/`confirmed`) nas tabelas que referenciam arquivos? | Não na v1; reavaliar após ver a frequência de parciais nos logs. |
| 2 | Quais tabelas/colunas referenciam arquivos (e em que formato: `bucket`+`path`, só `path`, URL)? Define os contratos da seção 5. | Guardar sempre `bucket` + `path`, nunca a URL (a URL é derivável e pode mudar). |
| 3 | Os caminhos dos arquivos são definidos por quem chama ou gerados pela integração? | Derivados de um id estável fornecido pelo chamador (idempotência). |
| 4 | O upload deve usar *upsert* (sobrescrever) por padrão ou falhar se existir? | Falhar por padrão; *upsert* explícito por operação. |
| 5 | Substituir arquivo mantém o mesmo caminho (sobrescreve) ou usa caminho novo e apaga o antigo? | Caminho novo + apagar o antigo depois (nunca deixa link quebrado). |
| 6 | Quem deve ser avisado de uma operação `parcial`: só log, ou também um canal (alerta)? | Só log estruturado na v1. |
| 7 | Há volume/valor que justifique a rotina de limpeza já na v1? | Não; começar pela limpeza manual guiada pelos logs. |
| 8 | As operações compostas podem ser assíncronas (concorrência entre etapas)? | Sequenciais; concorrência só dentro de lotes, e fora da v1. |

## 13. Referências

- Visão geral do projeto: [spec.md](../spec.md)
- Variáveis de ambiente: [01-variaveis-de-ambiente.md](01-variaveis-de-ambiente.md)
- Supabase, exclusão de dados no Postgres: <https://supabase.com/docs/guides/database/postgres/data-deletion>
- Supabase, controle de acesso do Storage: <https://supabase.com/docs/guides/storage/security/access-control>
- Supabase, uso e tamanho de Storage: <https://supabase.com/docs/guides/platform/manage-your-usage/storage-size>
- Consultar na etapa de especificação da Frente B (a confirmar contra a versão atual): documentação de upload (opção *upsert*, erro quando o objeto existe) e de exclusão de objetos do Storage, em <https://supabase.com/docs/guides/storage>. A recomendação de apagar objetos pela API de Storage, e não por SQL direto nas tabelas internas, deve ser verificada ali.
