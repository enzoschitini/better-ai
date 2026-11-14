# Segurança de dados — Chaves, RLS, Storage, validação e logs

> **Material de pesquisa (refinamento técnico).** A visão geral citada aqui como "00" / "visão geral" agora vive em [../spec.md](../spec.md). As "Questões em aberto" deste arquivo estão **consolidadas e resolvidas em [../decisions.md](../decisions.md)**, que prevalece em caso de divergência. Tarefas de implementação: [../tasks.md](../tasks.md).

> Status: **rascunho de planejamento** (nenhum código escrito ainda).
> Complementa [spec.md](../spec.md) e [01-variaveis-de-ambiente.md](01-variaveis-de-ambiente.md). Itens marcados como **[PROPOSTA]** são sugestões a validar; decisões pendentes estão em "Questões em aberto".
> Os fatos sobre o Supabase vêm da documentação oficial consultada (ver "Referências"). O Supabase renomeia recursos com frequência; reconferir antes de implementar.

## 1. Contexto e premissas

A integração (três classes: tabelas, arquivos e fachada integradora) roda **somente no backend** e é independente do código existente do projeto. Premissas deste documento:

- O consumidor é o backend, não o usuário final; a integração não implementa Supabase Auth (fora de escopo, ver visão geral, seção 5).
- A integração **não** altera schema, políticas RLS, grants nem configuração de buckets (somente leitura/escrita de dados e arquivos). **[PROPOSTA]**
- Segurança é responsabilidade em camadas: (1) a plataforma (RLS, grants, políticas de bucket), (2) a integração (validação, allowlist, redação de logs), (3) o código chamador (autorização de quem pode fazer o quê).

## 2. Modelo de chaves

### 2.1 O que diz a documentação oficial

| Chave | Formato | Papel Postgres | Comportamento |
|---|---|---|---|
| **Publishable** | `sb_publishable_...` | `anon` (ou `authenticated` com usuário logado) | Baixo privilégio; sujeita a RLS e grants. Pode ir para navegador, mobile e código-fonte. |
| **Secret** | `sb_secret_...` | `service_role` (atributo `BYPASSRLS`) | **Ignora todas as políticas RLS** e dá acesso irrestrito às APIs de Storage. Só em backend controlado. |
| **Legacy `anon` / `service_role`** | JWTs de longa duração | idem | Em descontinuação até o fim de 2026. Criar chaves novas **não** desativa as legadas; é preciso desativá-las à parte (Settings > API Keys). |

Detalhes úteis:

- As chaves novas não são JWT: devem ir no header `apikey`, não em `Authorization: Bearer`.
- A chave publishable **não protege** contra engenharia reversa, XSS, CSRF etc.; a segurança vem de RLS e grants corretos.
- Se a requisição carrega o token de um usuário logado, o RLS se aplica a esse usuário mesmo com cliente criado com chave secreta.
- O Supabase recomenda **uma chave secreta distinta por componente de backend**, para rotacionar um sem afetar os outros.

### 2.2 Qual chave usar em cada cenário do backend **[PROPOSTA]**

| Cenário | Chave | Justificativa |
|---|---|---|
| CRUD de tabelas por processos internos confiáveis (jobs, agentes, rotinas administrativas) | **Secret** | Backend não tem sessão de usuário; precisa operar independentemente de RLS. Exige autorização própria no código chamador. |
| Upload/exclusão em buckets privados feitos pelo backend | **Secret** | Idem; sem políticas em `storage.objects` o upload é negado por padrão. |
| Gerar URL assinada de leitura | **Secret** (backend) | A URL é gerada pelo servidor e entregue ao cliente por tempo limitado. |
| Ler arquivo de bucket **público** ou dado liberado por política `anon` | **Publishable** | Menor privilégio: não precisa de poder irrestrito. |
| Operar em nome de um usuário final (respeitando RLS) | **Publishable + token do usuário** | Fora do escopo atual; documentado só para evolução futura. |
| Testes automatizados | Projeto/branch **de teste** com chave própria | Nunca usar chaves de produção em testes. |

Recomendação: a fábrica (Factory) deve permitir criar o cliente em dois **modos de credencial** (`privileged` com secret, `restricted` com publishable) e **o modo padrão deve ser o de menor privilégio possível para a operação**, com escolha explícita e registrada em log (sem exibir a chave) quando se usa o modo privilegiado. Ver Questões em aberto, item 1.

## 3. Prevenção de vazamento da chave secreta

### 3.1 Regras (obrigatórias)

A chave secreta **nunca** pode aparecer em:

- **Frontend/clientes:** navegador (nem em localhost), apps distribuídos, variáveis estilo `NEXT_PUBLIC_*`. No Streamlit, nunca em `st.session_state`, `st.secrets` exibido ou componentes que enviem dados ao navegador.
- **Logs:** nem em debug. Se for estritamente necessário identificar uma chave, usar no máximo os 6 primeiros caracteres da parte aleatória ou um hash SHA-256 (recomendação oficial). **[PROPOSTA]** Padrão desta integração: registrar apenas o **tipo** da chave (`secret`/`publishable`) e um hash curto.
- **Respostas de API e mensagens de erro/exceções:** erros de domínio não devem carregar configuração, headers nem o objeto cliente.
- **Repositório:** código, `.env` versionado, documentação, testes, fixtures, mensagens de commit, issues, chat e e-mail. O `.env` real permanece no `.gitignore`; só o modelo de nomes (sem valores) é versionado.
- **URLs e query strings.**

### 3.2 Medidas técnicas **[PROPOSTA]**

1. **Objeto de configuração com segredo mascarado:** o campo da chave é um tipo "segredo" cujo `repr`/`str` devolve `***` e que só entrega o valor numa chamada explícita usada pelo adapter. Evita vazamento por `print(config)`, tracebacks e logs de depuração.
2. **Adapter é o único ponto que toca a chave.** As classes de tabelas, arquivos e a fachada nunca a recebem nem a expõem.
3. **Exceções saneadas:** o adapter captura erros do SDK e converte em erros de domínio **sem** reanexar headers, URLs com parâmetros sensíveis ou `__cause__` com dados de configuração em mensagens exibíveis.
4. **Fail-fast no carregamento:** se a variável esperada estiver ausente ou parecer de tipo errado (ex.: chave publishable onde se pede secret), falhar na inicialização com mensagem que cita apenas o **nome** da variável.
5. **Varredura de segredos no CI/pré-commit** (ex.: ferramenta de detecção de segredos) para padrões `sb_secret_`, `sb_publishable_` e JWTs. **[PROPOSTA]**
6. **Uma chave secreta por ambiente e por componente**; nunca compartilhar a de produção com dev/homol.
7. **Armazenamento:** variáveis do provedor de deploy (Railway) em vez de arquivos; `.env` só local.

## 4. RLS e políticas: o que a integração assume e o que fica fora

### 4.1 Fatos da plataforma

- Habilitar RLS não basta: **grants** são separados e verificados antes das políticas (ausência de grant gera erro `42501`). Com RLS ativo e sem políticas, a chave publishable não vê linhas.
- Em projetos existentes, tabelas novas em `public` podem nascer com todos os privilégios para `anon`/`authenticated`/`service_role`; recomenda-se revogar de `anon`/`authenticated` e conceder só o necessário.
- Tabelas criadas pelo Dashboard têm RLS ligado; as criadas via SQL Editor ou outras ferramentas **não**.
- Views rodam como dono e podem contornar RLS; em Postgres 15+ usar `security_invoker = true`.
- Boa prática oficial: expor via Data API só um schema dedicado (ex.: `api`) e manter tabelas internas em schemas não expostos.

### 4.2 O que a integração assume **[PROPOSTA]**

1. O backend usa a chave secreta para operações administrativas, portanto **o RLS não é a barreira dessas operações**. A barreira passa a ser: allowlist (seção 6), autorização no chamador e validação de entrada.
2. As tabelas acessadas existem e já têm RLS habilitado como defesa em profundidade (útil se a chave publishable vazar ou for usada no futuro).
3. Em modo `restricted` (publishable), o resultado depende 100% das políticas existentes; a integração apenas traduz erros de permissão em erro de domínio (ex.: `PermissionDenied`).

### 4.3 Fora do escopo

- Criar/alterar tabelas, políticas RLS, grants, views, funções `security definer` e configurações de bucket (seriam migrations/DDL; ver visão geral, seção 5).
- Autorização por usuário final e Supabase Auth.
- Rate limiting e cotas via pre-request function (`pgrst.db_pre_request`) do PostgREST; observar que esse gancho não cobre Storage nem Realtime.

### 4.4 Recomendação de acompanhamento

Criar, **fora desta integração**, um checklist de configuração do projeto Supabase (RLS ligado em todas as tabelas expostas, grants mínimos, buckets revisados) e rodar os "advisors" de segurança do Supabase periodicamente.

## 5. Buckets e URLs

### 5.1 Público x privado

| Aspecto | Bucket público | Bucket privado (padrão) |
|---|---|---|
| Leitura/download | Qualquer pessoa com a URL; controle de acesso **ignorado** para servir arquivos | Governada por RLS ou por URL assinada |
| Escrita, exclusão, move, copy | Continuam exigindo controle de acesso | Idem |
| Caching/CDN | Melhor desempenho | Cache diferente |
| Uso indicado | Conteúdo realmente público (logos, blog) | Documentos, áudio/vídeo de clientes, qualquer dado pessoal |

Observações oficiais: uploads sem políticas em `storage.objects` são negados por padrão em buckets privados; `upsert` exige também permissões de `SELECT` e `UPDATE`; a chave secreta ignora essas políticas.

### 5.2 URL pública x URL assinada **[PROPOSTA]**

- **Padrão: privado + URL assinada.** Só marcar bucket como público quando o conteúdo puder ser lido por qualquer pessoa na internet, indefinidamente, e o caminho do objeto não for segredo. Uma URL pública não expira nem é revogável sem apagar/mover o arquivo.
- A fachada deve expor operações distintas e nomeadas para evitar erro: "obter URL pública" (falha se o bucket não for público) e "obter URL assinada" (exige `expires_in`).
- Pseudo-assinatura: `signed_url(bucket, path, expires_in_seconds, download=False) -> str`. `expires_in` é em **segundos** (obrigatório na API oficial; ex.: 60 = 1 minuto).

### 5.3 Tempo de expiração **[PROPOSTA]**

| Uso | Expiração sugerida |
|---|---|
| Exibir/baixar imediatamente numa resposta de API | 60 a 300 s |
| Link enviado ao usuário para download posterior | até 3600 s (1 h) |
| Maior que 1 dia | **Proibido por padrão**; exige parâmetro de configuração explícito |

A integração deve ter um **teto configurável** (padrão 3600 s) e um **valor padrão** (padrão 300 s), rejeitando valores `<= 0` ou acima do teto. A documentação oficial consultada não informa um máximo de expiração; confirmar ao implementar.

- Nunca gravar URLs assinadas no banco como se fossem permanentes; gravar o **caminho (bucket + path)** e gerar a URL sob demanda.
- URLs assinadas contêm token: tratá-las como segredo de curta duração (redigir nos logs, ver seção 9).

## 6. Validação de entrada: tabelas, colunas, filtros e buckets

O cliente do Supabase (PostgREST) parametriza valores, o que reduz o risco de injeção SQL clássica, mas **nomes de tabela, coluna, operadores, ordenação e caminhos de arquivo podem ser controlados por entrada externa** e viram parte da URL/consulta. Por isso:

### 6.1 Allowlist de tabelas e buckets (obrigatória) **[PROPOSTA]**

- A configuração declara explicitamente as tabelas permitidas (e o schema) e os buckets permitidos. Qualquer outro nome é rejeitado **antes** de qualquer chamada à rede, com erro de domínio (`TabelaNaoPermitida`, `BucketNaoPermitido`).
- Opcionalmente, por tabela: allowlist de colunas selecionáveis/filtráveis/ordenáveis e quais operações (leitura, escrita, exclusão) são permitidas. Isso materializa o princípio do menor privilégio na aplicação, já que a chave secreta não tem limite próprio.
- Nomes que não passarem na allowlist **não** devem ser ecoados em mensagens de erro de forma sem tratamento (evitar reflexão de entrada maliciosa); registrar versão truncada/escapada.

### 6.2 Validação de formato

- Identificadores (tabela, coluna, bucket): regex restritiva, por exemplo `^[a-z_][a-z0-9_]{0,62}$` (limite de 63 bytes do Postgres), aplicada **além** da allowlist.
- Colunas em `select`, `order` e filtros: devem pertencer à allowlist da tabela; rejeitar `*` irrestrito quando houver allowlist de colunas sensíveis.
- Operadores de filtro: conjunto fechado (`eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`, `is`, `like`/`ilike` conforme decisão). Rejeitar operadores desconhecidos.
- **Nunca** montar strings de filtro concatenando entrada (ex.: expressões `or=(...)` do PostgREST). Se for preciso `or`, construí-lo a partir de estruturas já validadas, escapando valores. Valores com vírgula, parênteses ou pontos são especialmente perigosos nessas expressões.
- Paginação: `limit` com teto (ex.: 1000) e `offset` não negativo; ordenação só por colunas permitidas. Evita consultas abusivas.
- Atualizar/deletar **sempre exigem filtro**. Update/delete sem filtro afeta a tabela inteira; a integração deve recusar por padrão (e permitir somente via parâmetro explícito e logado). **[PROPOSTA]**
- Lote (insert em massa): limite de quantidade de registros e de tamanho do payload.
- Campos desconhecidos no payload de escrita: rejeitar (mass assignment) quando houver esquema de colunas permitidas.

### 6.3 Exemplo de cenários

| Entrada | Resultado esperado |
|---|---|
| `tabela="usuarios; drop table x"` | Rejeitada pela regex e pela allowlist; nada vai à rede. |
| `tabela="segredos_internos"` (não listada) | `TabelaNaoPermitida`; log em WARNING sem dados do payload. |
| `ordenar_por="senha_hash"` (coluna fora da allowlist) | Rejeitada. |
| `delete(tabela="logs", filtros={})` | Recusada: filtro obrigatório. |
| `limite=10_000_000` | Reduzido ao teto ou rejeitado (decidir); nunca repassado como veio. |

## 7. Arquivos: nomes, caminhos, MIME e tamanho

### 7.1 Sanitização de nomes e caminhos (path traversal) **[PROPOSTA]**

Regras sobre o **caminho do objeto** dentro do bucket:

1. Normalizar para Unicode NFC e rejeitar caracteres de controle e bytes nulos.
2. Rejeitar segmentos `.` e `..`, caminhos absolutos (começando com `/`), barras invertidas `\`, letras de unidade (`C:`) e sequências codificadas (`%2e%2e`, `%2f`) **após decodificar** uma única vez; rejeitar dupla codificação.
3. Permitir apenas um conjunto seguro: letras, números, `-`, `_`, `.` e `/` como separador de pastas controlado pelo sistema; demais caracteres substituídos ou rejeitados (decisão: ver questões em aberto).
4. Limitar comprimento do nome (ex.: 255 bytes) e profundidade de pastas (ex.: 8).
5. **Não confiar no nome enviado pelo cliente.** Preferência: gerar o caminho no servidor (ex.: `<prefixo-da-entidade>/<uuid4>.<ext-validada>`) e guardar o nome original apenas como metadado/coluna, após sanitizado. Isso também evita colisões e sobrescrita acidental.
6. O prefixo (pasta) vem de lógica do backend (tenant, entidade), nunca direto de entrada externa sem validação.
7. Proteção de sobrescrita: `upsert` desligado por padrão; ligar só por parâmetro explícito (sobrescrever exige também `SELECT`/`UPDATE` em `storage.objects` para chaves restritas).
8. Em operações de **delete** e **download**, aplicar a mesma sanitização e confirmar que o caminho resultante está dentro do prefixo esperado.

### 7.2 Tipo MIME e tamanho

- A plataforma permite restrições **por bucket** (tamanho máximo e tipos permitidos), definidas na criação/configuração do bucket; elas são a barreira de último recurso e ficam fora do escopo da integração (que não administra buckets). Recomendação: configurá-las no Supabase **e** validar na integração (defesa em profundidade). **[PROPOSTA]**
- Validação na integração antes do upload:
  1. **Tamanho:** checar antes de enviar, com limite por bucket vindo da configuração (ex.: imagem 10 MB, áudio 50 MB, vídeo conforme decisão). Para fluxos em streaming, contar bytes durante a leitura e abortar ao exceder.
  2. **MIME declarado x extensão:** a extensão deve ser coerente com o MIME permitido para aquele bucket (tabela allowlist `mime -> extensões`).
  3. **Detecção por conteúdo (magic bytes):** conferir assinatura inicial do arquivo contra o MIME declarado; rejeitar se divergir. O MIME informado pelo cliente (`Content-Type`) nunca é fonte confiável.
  4. **Tipos perigosos servidos de bucket público** (HTML, SVG com script, JS, executáveis): bloquear por padrão, pois podem executar script no domínio de origem; se necessários, usar bucket privado e `download=True` na URL assinada.
- Limites de arquivos vazios (0 bytes) e de quantidade por requisição.
- Antivírus/varredura de malware: fora do escopo, registrado como risco aceito até decisão. Ver questões em aberto.

### 7.3 Exemplo de cenários

| Entrada | Resultado esperado |
|---|---|
| Nome `../../outro-bucket/x.png` | Rejeitado por traversal; caminho real gerado pelo servidor. |
| `foto.png` com conteúdo de executável | Rejeitado: magic bytes não correspondem. |
| Upload de 200 MB em bucket com limite de 10 MB | Rejeitado antes de enviar (erro `ArquivoGrandeDemais`). |
| Mesmo nome enviado duas vezes | Caminhos distintos (uuid); sem sobrescrita. |
| `bucket="documentos-internos"` fora da allowlist | `BucketNaoPermitido`. |

## 8. Princípio do menor privilégio **[PROPOSTA]**

- Modo de credencial mínimo por operação (seção 2.2) e chave separada por componente/ambiente.
- Allowlist de tabelas, colunas, operações e buckets (seção 6). Cada contrato expõe só os métodos necessários (Segregação de Interfaces): um consumidor que só lê recebe uma interface somente leitura, sem insert/delete.
- A fachada pode ser instanciada em **modo somente leitura**, que bloqueia métodos de escrita localmente.
- Operações destrutivas (delete, update em lote, upsert) exigem parâmetros explícitos e geram log em nível mais alto (WARNING).
- No Supabase: revisar grants (revogar de `anon`/`authenticated` o que não for necessário), usar schema dedicado exposto e manter RLS ligado. Isso é fora do escopo da integração, mas deve constar no checklist de configuração.

## 9. Redação de dados sensíveis nos logs

Complementa a seção 3.2 da visão geral.

- **Lista de campos sensíveis** (configurável): `apikey`, `authorization`, `token`, `access_token`, `refresh_token`, `secret`, `password`, `senha`, `cookie`, chaves com prefixo `sb_secret_`/`sb_publishable_`, JWTs (três segmentos base64 separados por ponto) e o parâmetro `token` de URLs assinadas.
- **Redator central**, aplicado pelo logger **antes** de formatar: percorre dicionários e listas aninhadas e substitui valores por `***` (ou hash curto). Aplicado também a strings livres via regex dos padrões de chave/JWT.
- **Payloads de registros e conteúdo de arquivos nunca são logados** por padrão: registrar apenas metadados (tabela, bucket, caminho saneado, quantidade de linhas, tamanho em bytes, MIME, duração, resultado). Nível `DEBUG` pode incluir os **nomes** das colunas, mas não os valores, a menos que haja flag explícita de depuração insegura, desligada por padrão e proibida em produção. **[PROPOSTA]**
- Dados pessoais (e-mail, CPF etc.): redigir ou mascarar (ex.: `j***@dominio.com`) quando aparecerem em filtros logados.
- URLs assinadas: registrar sem a query string (`?token=...`).
- Cores e formatação não podem contornar a redação (a redação ocorre antes da formatação).
- Testar o redator com exemplos de chaves e JWTs fictícios e verificar que não sobram nos logs capturados.

## 10. Rotação de chaves e resposta a vazamento

### 10.1 Rotação preventiva **[PROPOSTA]**

- Periodicidade sugerida: a cada 90 dias e **sempre** quando alguém com acesso sair do projeto.
- Com as novas chaves de API do Supabase é possível ter chaves secretas separadas por componente, o que permite rotação sem derrubar tudo: criar a nova, publicar no provedor de deploy, validar, depois revogar a antiga.
- Planejar o carregamento de configuração para que a troca seja só alteração de variável de ambiente e reinício, sem mudança de código.
- Desativar as chaves legadas (`anon`/`service_role` JWT) depois da migração; lembrar que isso é feito separadamente.

### 10.2 Se uma chave vazar

1. **Conter:** gerar uma nova chave secreta e **revogar a antiga imediatamente** (Dashboard, CLI ou Management API, seguindo o guia oficial de rotação de chave vazada). Se for a chave legada, rotacionar o segredo JWT conforme a documentação.
2. Atualizar a variável nos ambientes afetados e reimplantar; confirmar que o serviço voltou a funcionar.
3. **Remover a causa** (commit, log, resposta de API, mensagem de chat). Remover do histórico do Git não substitui a revogação: considerar a chave comprometida mesmo após limpeza.
4. **Investigar uso indevido:** revisar logs do Supabase (API, Auth, Storage) no período de exposição; verificar linhas/arquivos alterados ou baixados e custos anormais.
5. **Avaliar impacto:** se houve acesso a dados pessoais, acionar o responsável por privacidade/LGPD.
6. **Registrar o incidente** e a correção preventiva (por exemplo, regra de varredura de segredos).
7. Nesta integração: o agente que detectar a exposição **avisa o usuário para rotacionar** (conforme guia de variáveis, seção 5) e **não** rotaciona por conta própria.

## 11. Checklist de segurança para revisão de código

**Credenciais**
- [ ] Nenhum valor de chave em código, testes, fixtures, docs, commits ou logs.
- [ ] A chave só é lida pelo adapter; o tipo "segredo" mascara `repr`/`str`.
- [ ] Modo de credencial (secret x publishable) é o mínimo necessário e está documentado no ponto de uso.
- [ ] Falhas de configuração citam só o **nome** da variável.
- [ ] Nada do Streamlit/FastAPI devolve configuração ou objeto cliente ao navegador.

**Tabelas**
- [ ] Tabela e colunas validadas por regex **e** allowlist antes de qualquer chamada.
- [ ] Operadores de filtro de conjunto fechado; sem concatenação de strings em filtros.
- [ ] Update/delete exigem filtro; operações em massa são explícitas e logadas.
- [ ] `limit` com teto; ordenação restrita a colunas permitidas.
- [ ] Campos desconhecidos no payload rejeitados.

**Arquivos**
- [ ] Bucket validado por allowlist; padrão privado.
- [ ] Caminho gerado/sanitizado no servidor; sem `..`, `/` inicial, `\`, unidade, bytes nulos nem dupla codificação.
- [ ] Tamanho e MIME validados (declarado, extensão e magic bytes); tipos executáveis bloqueados.
- [ ] `upsert` desligado por padrão.
- [ ] URLs assinadas com expiração dentro do teto; URL não persistida como permanente.
- [ ] Bucket público só com conteúdo realmente público.

**Logs e erros**
- [ ] Redação central ativa antes da formatação; payloads e conteúdo de arquivos não registrados.
- [ ] Exceções de domínio sem headers, chaves ou URLs com token.
- [ ] Mensagens de erro para o chamador não revelam estrutura interna (nomes de tabelas fora da allowlist, stack do SDK).

**Processo**
- [ ] `.env` fora do Git; modelo versionado só com nomes.
- [ ] Varredura de segredos no CI/pré-commit.
- [ ] Plano de rotação e de resposta a vazamento conhecido pela equipe.
- [ ] Testes cobrem casos negativos: traversal, MIME falso, tabela fora da allowlist, filtro vazio, expiração inválida, vazamento em log.

## 12. Critérios de aceite

1. Nenhuma chave aparece em saída de logs, exceções, `repr` de objetos de configuração ou respostas de API (verificado por testes automatizados com chaves fictícias).
2. Chamadas com tabela/coluna/bucket fora da allowlist falham **sem** tráfego de rede.
3. Entradas de path traversal e dupla codificação são rejeitadas em upload, download e delete.
4. Upload excedendo tamanho ou com MIME/magic bytes inconsistentes é rejeitado antes do envio.
5. URL assinada respeita o teto de expiração; valores inválidos são recusados.
6. Update/delete sem filtro são recusados por padrão.
7. A fachada pode ser criada em modo somente leitura, que bloqueia escrita localmente.
8. Há documentação de rotação e de resposta a vazamento aprovada pelo responsável do projeto.

## 13. Questões em aberto

| # | Questão | Recomendação |
|---|---|---|
| 1 | Usar só a chave secreta ou oferecer também o modo `restricted` (publishable)? | Oferecer os dois modos na Factory; padrão secret para o backend atual, publishable apenas para leitura de buckets/tabelas explicitamente públicos. |
| 2 | Quais tabelas e colunas entram na allowlist inicial? | Começar só pelos primeiros casos de uso reais (visão geral, questão 8), com allowlist de colunas para tabelas com dados pessoais. |
| 3 | Buckets: quais são públicos? Algum deveria ser privado? | Tratar todos como privados até confirmação; só manter público o que for realmente público. |
| 4 | Teto e padrão de expiração das URLs assinadas | 300 s padrão, 3600 s teto; exceções por configuração. |
| 5 | Limites de tamanho/tipo por bucket | Definir tabela `bucket -> (tamanho máx, MIME/extensões)` na configuração e espelhar na configuração dos buckets no Supabase. |
| 6 | Nomes de arquivo: rejeitar ou substituir caracteres inválidos? | Gerar caminho no servidor com uuid; guardar nome original saneado como metadado. |
| 7 | Varredura antivírus de uploads é necessária? | Fora do escopo agora; reavaliar se houver upload de usuários externos. |
| 8 | Reutilizar variáveis `SUPABASE_*` existentes ou usar nomes novos? | Nomes próprios e isolados (alinha com independência da integração atual); decisão compartilhada com o doc 01. |
| 9 | Periodicidade de rotação e responsável | 90 dias; responsável a definir pelo usuário. |
| 10 | Haverá política de ambientes (projetos Supabase distintos por dev/homol/prod)? | Sim, chaves e projetos separados; nunca chave de produção em dev. |

## 14. Referências

- Chaves de API (publishable/secret, legadas, restrições): <https://supabase.com/docs/guides/api/api-keys>
- Row Level Security (grants, bypass, views): <https://supabase.com/docs/guides/database/postgres/row-level-security>
- Protegendo a Data API (schemas expostos, grants, pre-request): <https://supabase.com/docs/guides/api/securing-your-api>
- Controle de acesso do Storage: <https://supabase.com/docs/guides/storage/security/access-control>
- Fundamentos de buckets (público x privado): <https://supabase.com/docs/guides/storage/buckets/fundamentals>
- Referência `createSignedUrl` (expiração em segundos): <https://supabase.com/docs/reference/javascript/storage-from-createsignedurl>
- Documentos do projeto: [spec.md](../spec.md), [01-variaveis-de-ambiente.md](01-variaveis-de-ambiente.md)
