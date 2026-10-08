import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { Snapshot, Tally, TurnReport } from '../types'
import { addUsage, describeSession, describeTurn, lastLine, mergeTallies, sessionLine, snapshot } from './format'

const last = atom({ plugin: 'creditos', key: 'last' } as const, null)
const live = atom({ plugin: 'creditos', key: 'live' } as const, null)
const prompts = atom({ plugin: 'creditos', key: 'prompts' } as const, 0)
const sessionMain = atom({ plugin: 'creditos', key: 'sessionMain' } as const, [])
const sessionSubagents = atom({ plugin: 'creditos', key: 'sessionSubagents' } as const, [])
const isHidden = atom({ plugin: 'creditos', key: 'isHidden' } as const, false)

export const register: Register = on => {
  // The prompt in flight: reset at each main-loop turn.start, reported at its turn.complete.
  let main: Tally[] = []
  let subagents: Tally[] = []
  let before: Snapshot | null = null

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'creditos',
      description: 'Mostra o consumo de créditos da sessão, por modelo, e reexibe a faixa',
    })
    const now = snapshot(await $.session.usage())
    await update($, live, () => now)

    return next(e)
  })

  on('turn.start', async ($, e, next) => {
    main = []
    subagents = []
    before = snapshot(await $.session.usage())

    return next(e)
  })

  // Every model request, main loop and subagents alike, with what it cost.
  on('turn.step', async function* ($, e, next) {
    const result = yield* next(e)
    if (result.usage !== null) {
      if (e.agentId === undefined) {
        main = addUsage(main, result.usage.model, result.usage)
      } else {
        subagents = addUsage(subagents, result.usage.model, result.usage)
      }
    }

    return result
  })

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    if (e.agentId !== undefined) {
      return result
    }

    const now = snapshot(await $.session.usage())
    const turn: TurnReport = {
      durationMs: e.durationMs,
      costUsd: now.usd !== null && before?.usd != null ? Math.max(0, now.usd - before.usd) : null,
      main,
      subagents,
    }
    const text = describeTurn(turn, now, before, await $.clock.now())

    await update($, prompts, n => n + 1)
    await update($, sessionMain, list => mergeTallies(list, turn.main))
    await update($, sessionSubagents, list => mergeTallies(list, turn.subagents))
    await update($, last, () => turn)
    await update($, live, () => now)
    main = []
    subagents = []
    before = null

    return { ...result, text }
  })

  on('session.measure', async ($, e, next) => {
    const now = snapshot(e)
    await update($, live, () => now)

    return next(e)
  })

  on('session.end', async ($, e, next) => {
    if (e.reason === 'clear') {
      await update($, prompts, () => 0)
      await update($, sessionMain, () => [])
      await update($, sessionSubagents, () => [])
      await update($, last, () => null)
    }

    return next(e)
  })

  on('command.run', { command: 'creditos' }, async $ => {
    await update($, isHidden, () => false)
    const text = describeSession(
      await read($, live),
      await read($, prompts),
      await read($, sessionMain),
      await read($, sessionSubagents),
      await $.clock.now(),
    )

    return { text }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey || (await read($, isHidden))) {
      return next(e)
    }
    const turn = await read($, last)
    const snap = await read($, live)
    if (turn === null && snap === null) {
      return next(e)
    }

    const { Box, Button, Text } = $.ui.resolve(e)

    return (
      <Box flexDirection="column">
        <Box>
          <Text dimColor>{turn === null ? 'Créditos: aguardando o primeiro prompt ' : `${lastLine(turn)} `}</Text>
          <Button key="ocultar" label="Ocultar" onPress={() => update($, isHidden, () => true)} />
        </Box>
        {snap !== null && <Text dimColor>{sessionLine(snap)}</Text>}
      </Box>
    )
  })
}
