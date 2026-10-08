/** Tokens and requests one model spent, summed. */
export type Tally = {
  model: string
  requests: number
  input: number
  output: number
  cacheRead: number
  cacheWrite: number
}

/** One rate-limit window as the last API response reported it. */
export type Limit = {
  kind: string
  percentUsed: number
  resetsAt?: string
}

/** The session's figures at one moment: cost, context fill, limits. */
export type Snapshot = {
  usd: number | null
  contextPercent: number | null
  contextTokens: number | null
  contextWindow: number
  limits: Limit[]
}

/** What one prompt (one main-loop turn) consumed. */
export type TurnReport = {
  durationMs: number
  costUsd: number | null
  main: Tally[]
  subagents: Tally[]
}

declare module 'claude-code' {
  interface PluginState {
    creditos: {
      last: TurnReport | null
      live: Snapshot | null
      prompts: number
      sessionMain: Tally[]
      sessionSubagents: Tally[]
      isHidden: boolean
    }
  }
}
