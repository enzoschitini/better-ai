# Spec: integração Supabase

Especificação seguindo **Spec-Driven Development (SDD)** para a nova integração do backend com o Supabase, isolada em `supabase/` e independente da integração existente.

## Como navegar (ordem de leitura)

| # | Documento | Pergunta que responde |
|---|---|---|
| 1 | [constitution.md](constitution.md) | Quais princípios nunca podem ser violados? |
| 2 | [spec.md](spec.md) | **O quê** e **por quê**: objetivo, histórias, requisitos, fora de escopo, critérios de sucesso |
| 3 | [decisions.md](decisions.md) | O que já foi decidido, o que **precisa da sua confirmação** e como as contradições foram resolvidas |
| 4 | [plan.md](plan.md) | **Como**: arquitetura, estrutura de pastas, contratos, riscos, rastreabilidade |
| 5 | [tasks.md](tasks.md) | Em que ordem implementar, com dependências e critérios |
| 6 | [research/](research/) | Pesquisa e refinamento técnico de cada tema (apoio, não fonte de decisão) |

## Pesquisa de apoio

| Arquivo | Tema |
|---|---|
| [01](research/01-variaveis-de-ambiente.md) | Guia para obter credenciais e dados na plataforma Supabase (uso do Chrome, somente leitura) |
| [02](research/02-tratamento-de-erros-e-resiliencia.md) | Exceções, timeout, retry, logs de erro |
| [03](research/03-configuracao-centralizada.md) | Configuração imutável, variáveis, ambientes |
| [04](research/04-estrategia-de-testes.md) | Pirâmide de testes, fakes, integração, cobertura |
| [05](research/05-seguranca-de-dados.md) | Chaves, RLS, URLs assinadas, validação, checklist |
| [06](research/06-modelagem-de-dados.md) | Registros, Query Object, tipos, descritor de tabela |
| [07](research/07-arquivos-grandes-e-storage.md) | Upload/download, validação, nomes, colisão |
| [08](research/08-consistencia-entre-frentes.md) | Operações combinadas arquivo + registro |
| [09](research/09-lote-e-paginacao.md) | Lote, paginação, iteração |

## Regra de precedência
`constitution` > `decisions` > `spec` > `plan` > `tasks` > `research`. Em divergência, vale o documento mais à esquerda.

## Status
Planejamento concluído. **Próximo passo:** Fase 0 de [tasks.md](tasks.md) (confirmar D-01 a D-08). Nenhum código foi escrito.
