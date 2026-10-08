import type { ModelUsage, SessionUsage } from 'claude-code'

import type { Limit, Snapshot, Tally, TurnReport } from '../types'

const LIMIT_NAMES: Record<string, string> = {
  five_hour: 'Limite 5h',
  seven_day: 'Limite semanal',
  seven_day_opus: 'Limite semanal (Opus)',
  seven_day_sonnet: 'Limite semanal (Sonnet)',
  spend_limit: 'Limite de gasto',
}

const SHORT_LIMIT_NAMES: Record<string, string> = {
  five_hour: '5h',
  seven_day: 'semanal',
  seven_day_opus: 'semanal Opus',
  seven_day_sonnet: 'semanal Sonnet',
  spend_limit: 'gasto',
}

export const tokens = (n: number): string =>
  n >= 1_000_000
    ? `${(n / 1_000_000).toFixed(2)}M`
    : n >= 1_000
      ? `${(n / 1_000).toFixed(1)}k`
      : String(n)

export const dollars = (n: number): string =>
  n >= 1 ? `$${n.toFixed(2)}` : n >= 0.01 ? `$${n.toFixed(3)}` : `$${n.toFixed(4)}`

export const duration = (ms: number): string => {
  const s = Math.round(ms / 1000)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  return m < 60 ? `${m}min ${s % 60}s` : `${Math.floor(m / 60)}h ${m % 60}min`
}

const until = (iso: string, now: number): string | null => {
  const ms = Date.parse(iso) - now
  if (!Number.isFinite(ms) || ms <= 0) return null
  const min = Math.ceil(ms / 60_000)
  if (min < 60) return `${min}min`
  const h = Math.floor(min / 60)
  return h < 24 ? `${h}h ${min % 60}min` : `${Math.floor(h / 24)}d ${h % 24}h`
}

const percent = (n: number): string => `${Math.round(n * 10) / 10}%`

const shortModel = (model: string): string => model.replace(/^claude-/, '')

const plural = (n: number, one: string, many: string): string => `${n} ${n === 1 ? one : many}`

export const emptyTally = (model: string): Tally => ({
  model,
  requests: 0,
  input: 0,
  output: 0,
  cacheRead: 0,
  cacheWrite: 0,
})

/** Adds one response's (or a summed tally's) usage to the model's row. */
export const addUsage = (list: readonly Tally[], model: string, usage: ModelUsage, requests = 1): Tally[] => {
  const base = list.find(t => t.model === model) ?? emptyTally(model)
  const sum: Tally = {
    model,
    requests: base.requests + requests,
    input: base.input + usage.input_tokens,
    output: base.output + usage.output_tokens,
    cacheRead: base.cacheRead + usage.cache_read_input_tokens,
    cacheWrite: base.cacheWrite + usage.cache_creation_input_tokens,
  }
  return list.some(t => t.model === model) ? list.map(t => (t.model === model ? sum : t)) : [...list, sum]
}

export const mergeTallies = (into: readonly Tally[], from: readonly Tally[]): Tally[] =>
  from.reduce<Tally[]>(
    (acc, t) =>
      addUsage(
        acc,
        t.model,
        {
          input_tokens: t.input,
          output_tokens: t.output,
          cache_read_input_tokens: t.cacheRead,
          cache_creation_input_tokens: t.cacheWrite,
        },
        t.requests,
      ),
    [...into],
  )

export const snapshot = (u: Pick<SessionUsage, 'context' | 'rateLimits' | 'cost'>): Snapshot => ({
  usd: u.cost?.usd ?? null,
  contextPercent: u.context.percent ?? null,
  contextTokens: u.context.tokens ?? null,
  contextWindow: u.context.window,
  limits: u.rateLimits.map(l =>
    l.resetsAt === undefined
      ? { kind: l.kind, percentUsed: l.percentUsed }
      : { kind: l.kind, percentUsed: l.percentUsed, resetsAt: l.resetsAt },
  ),
})

const tallyTokens = (list: readonly Tally[]): number =>
  list.reduce((sum, t) => sum + t.input + t.output + t.cacheRead + t.cacheWrite, 0)

const tallyRequests = (list: readonly Tally[]): number => list.reduce((sum, t) => sum + t.requests, 0)

const tallyLine = (t: Tally): string =>
  `${shortModel(t.model)}: ${plural(t.requests, 'chamada', 'chamadas')} · entrada ${tokens(t.input)} · ` +
  `cache lido ${tokens(t.cacheRead)} · cache gravado ${tokens(t.cacheWrite)} · saída ${tokens(t.output)}`

const contextLine = (snap: Snapshot): string =>
  snap.contextPercent === null
    ? `Contexto: janela de ${tokens(snap.contextWindow)}`
    : `Contexto: ${percent(snap.contextPercent)} (${tokens(snap.contextTokens ?? 0)} de ${tokens(snap.contextWindow)})`

const limitLine = (limit: Limit, now: number, before: Limit | undefined): string => {
  let head = `${LIMIT_NAMES[limit.kind] ?? limit.kind}: ${percent(limit.percentUsed)}`
  if (before !== undefined) {
    const delta = Math.round((limit.percentUsed - before.percentUsed) * 10) / 10
    head += delta > 0 ? ` (+${delta} pts neste prompt)` : delta < 0 ? ' (a janela reiniciou)' : ' (sem mudança)'
  }
  const left = limit.resetsAt === undefined ? null : until(limit.resetsAt, now)
  return left === null ? head : `${head} · reseta em ${left}`
}

const tallyBullets = (main: readonly Tally[], subagents: readonly Tally[]): string[] => [
  ...main.map(t => `- Principal · ${tallyLine(t)}`),
  ...subagents.map(t => `- Subagentes · ${tallyLine(t)}`),
]

/** The report shown beneath each answer. */
export const describeTurn = (turn: TurnReport, now: Snapshot, before: Snapshot | null, clock: number): string => {
  const cost = turn.costUsd === null ? 'custo indisponível' : `${dollars(turn.costUsd)} (estimado)`
  const bullets = tallyBullets(turn.main, turn.subagents)
  const lines = [
    `Créditos deste prompt: ${cost} · ${duration(turn.durationMs)}`,
    '',
    ...(bullets.length === 0 ? ['- Nenhuma chamada ao modelo registrada'] : bullets),
    `- Sessão até agora: ${now.usd === null ? 'custo indisponível' : dollars(now.usd)} · ${contextLine(now)}`,
    ...now.limits.map(l => `- ${limitLine(l, clock, before?.limits.find(b => b.kind === l.kind))}`),
  ]
  return lines.join('\n')
}

/** What /creditos answers: the session so far. */
export const describeSession = (
  snap: Snapshot | null,
  prompts: number,
  main: readonly Tally[],
  subagents: readonly Tally[],
  clock: number,
): string => {
  const cost = snap?.usd == null ? 'custo indisponível' : `${dollars(snap.usd)} (estimado, a preço de API)`
  const bullets = tallyBullets(main, subagents)
  const lines = [
    `Consumo da sessão: ${cost}`,
    '',
    `Tokens desde que o mod carregou (${plural(prompts, 'prompt', 'prompts')}):`,
    '',
    ...(bullets.length === 0 ? ['- Nenhuma chamada ao modelo registrada ainda'] : bullets),
    ...(snap === null ? [] : [`- ${contextLine(snap)}`, ...snap.limits.map(l => `- ${limitLine(l, clock, undefined)}`)]),
  ]
  return lines.join('\n')
}

/** The band's first line: the last prompt in one glance. */
export const lastLine = (turn: TurnReport): string => {
  const all = [...turn.main, ...turn.subagents]
  const cache = all.reduce((sum, t) => sum + t.cacheRead, 0)
  const cost = turn.costUsd === null ? '' : `${dollars(turn.costUsd)} · `
  return (
    `Último prompt: ${cost}${plural(tallyRequests(all), 'chamada', 'chamadas')} · ` +
    `${tokens(tallyTokens(all))} tokens (${tokens(cache)} do cache) · saída ${tokens(all.reduce((s, t) => s + t.output, 0))}`
  )
}

/** The band's second line: the session and the plan's limits. */
export const sessionLine = (snap: Snapshot): string =>
  [
    `Sessão: ${snap.usd === null ? 'custo indisponível' : dollars(snap.usd)}`,
    snap.contextPercent === null ? null : `contexto ${percent(snap.contextPercent)}`,
    ...snap.limits.map(l => `${SHORT_LIMIT_NAMES[l.kind] ?? l.kind} ${percent(l.percentUsed)}`),
  ]
    .filter(part => part !== null)
    .join(' · ')
