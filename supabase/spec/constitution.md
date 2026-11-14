# Constituição da integração Supabase

Princípios **inegociáveis**. Toda decisão do [plano](plan.md), toda tarefa de [tasks.md](tasks.md) e toda revisão de código devem respeitá-los. Se uma tarefa exigir violar um princípio, a tarefa para e o princípio é rediscutido aqui primeiro.

## P1. Independência total
Todo o código novo vive em `supabase/` e **não importa nada** da integração Supabase existente no projeto (nem ela importa esta). O objetivo é testar e validar isoladamente antes de qualquer integração com o resto do sistema, que será uma fase separada com sua própria spec.

## P2. Três classes, uma responsabilidade cada
- **Classe de tabelas:** todo o CRUD de tabelas.
- **Classe de arquivos:** toda a manipulação de buckets.
- **Classe integradora (fachada):** compõe as duas, é o único ponto de entrada do backend, **não tem lógica de tabela nem de storage** e só orquestra.
- As duas primeiras **não se conhecem**.

## P3. SOLID e dependência de abstrações
O backend e a fachada dependem de **contratos** (interfaces), nunca de classes concretas nem do SDK do Supabase. Dependências entram por **injeção** no construtor. Contratos pequenos e específicos (segregação). Qualquer implementação de um contrato é substituível (inclusive fakes de teste). Extensão por adição, sem editar o que já funciona.

## P4. O SDK fica isolado atrás de um adapter
Nenhum módulo fora de `adapters/` importa `supabase`, `postgrest`, `storage3` ou `httpx`. Nenhuma exceção desses pacotes chega ao backend.

## P5. Falhar cedo, falhar claro
Configuração inválida falha **na criação** (Factory), listando **nomes** de variáveis, nunca valores. Entrada inválida falha antes de ir à rede.

## P6. Segredos nunca vazam
Chaves, JWTs, URLs assinadas completas, strings de conexão e conteúdo de arquivos/registros **não aparecem** em logs, exceções, mensagens, documentação ou commits. A chave secreta é de uso exclusivo do backend.

## P7. Logs claros, configuráveis e coloridos
Nível configurável (DEBUG/INFO/WARNING/ERROR) sem mexer em código. Verboso com detalhe útil (operação, recurso, duração, resultado) em **campos estruturados**, sem poluir. Cor por nível no terminal, mas o nível textual sempre presente. Cada erro é registrado **uma vez**, na fronteira que o trata. O logger é uma dependência injetada.

## P8. Erros do domínio, nunca do SDK
Hierarquia própria de exceções, com `__cause__` preservado. Retry em **um único lugar** (executor de resiliência) e só em operações idempotentes com erro recuperável.

## P9. Testável sem rede
Todo componente é testável com fakes por injeção. Testes de integração só rodam contra projeto de teste dedicado, **nunca contra produção**, e são pulados quando faltam credenciais.

## P10. Sem ações destrutivas ou fora de escopo
A integração **não** altera schema (DDL/migrations), **não** faz autenticação de usuários finais e **não** tem UI. Agentes que consultarem a plataforma Supabase fazem **somente leitura**, salvo pedido explícito.

## P11. Documentação viva
Mudou comportamento, mudou a spec na mesma alteração. Decisões novas entram em [decisions.md](decisions.md); a pesquisa de apoio fica em [research/](research/).
