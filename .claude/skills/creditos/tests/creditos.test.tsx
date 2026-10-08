import { expect, mock, test } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'
import type { On, SessionUsage, TurnStepResult } from 'claude-code'

const NOW = Date.parse('2026-10-08T12:00:00Z')

// The engine beneath the mod: a cost ledger and a 5h window that grow as the prompt runs.
const engine = (on: On) => {
  const figures = { usd: 1, fiveHour: 10 }
  mock.clock(on, { now: NOW })
  on('session.usage', () => {
    const value: SessionUsage = {
      startedAt: NOW - 3_600_000,
      context: { tokens: 88_000, window: 200_000, percent: 44 },
      rateLimits: [{ kind: 'five_hour', percentUsed: figures.fiveHour, resetsAt: '2026-10-08T15:12:00Z' }],
      cost: { usd: figures.usd },
    }
    return { value }
  })
  on('turn.start', ($, e) => ({ turnId: e.turnId }))
  on('turn.step', async function* ($, e): AsyncGenerator<never, TurnStepResult> {
    return {
      turnId: e.turnId,
      index: e.index,
      answer: '',
      toolUses: [],
      stopReason: 'end_turn',
      usage: {
        model: e.agentId === undefined ? 'claude-opus-5-5' : 'claude-haiku-5-5',
        input_tokens: 1_200,
        output_tokens: 2_300,
        cache_read_input_tokens: 88_400,
        cache_creation_input_tokens: 3_100,
      },
    }
  })
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('ui.render', { component: 'AbovePrompt' }, ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text key="engine">faixa do engine</Text>
  })

  return figures
}

const runPrompt = async ($: Engine, figures: { usd: number; fiveHour: number }) => {
  await $.turn.start({ text: 'oi', turnId: 't1' })
  for (const step of [
    { turnId: 't1', index: 0, model: 'claude-opus-5-5', messageCount: 1 },
    { turnId: 't1', index: 1, model: 'claude-opus-5-5', messageCount: 3 },
    { turnId: 's1', index: 0, model: 'claude-haiku-5-5', messageCount: 1, agentId: 'a1' },
  ]) {
    const stream = $.turn.step(step)
    for await (const _ of stream) {
      // drain
    }
  }
  figures.usd = 1.25
  figures.fiveHour = 12.5

  return $.turn.complete({ answer: 'pronto', durationMs: 42_000, isAborted: false, turnId: 't1', reason: 'answer' })
}

test('relata o consumo de cada prompt abaixo da resposta', async ($, on) => {
  const figures = engine(on)
  const done = await runPrompt($, figures)

  expect(done.text).toContain('Créditos deste prompt: $0.250 (estimado) · 42s')
  expect(done.text).toContain('- Principal · opus-5-5: 2 chamadas · entrada 2.4k · cache lido 176.8k · cache gravado 6.2k · saída 4.6k')
  expect(done.text).toContain('- Subagentes · haiku-5-5: 1 chamada')
  expect(done.text).toContain('- Sessão até agora: $1.25 · Contexto: 44% (88.0k de 200.0k)')
  expect(done.text).toContain('- Limite 5h: 12.5% (+2.5 pts neste prompt) · reseta em 3h 12min')
})

test('um subagente que termina não gera relatório', async ($, on) => {
  engine(on)
  const done = await $.turn.complete({ answer: 'relatório do subagente', durationMs: 1_000, isAborted: false, turnId: 's1', agentId: 'a1', reason: 'answer' })

  expect(done.text).toBe('relatório do subagente')
})

test('a faixa acima do prompt mostra o último prompt e se oculta', async ($, on) => {
  const figures = engine(on)
  await runPrompt($, figures)

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({
      plugin: 'creditos',
      surface,
      component: 'AbovePrompt',
      props: { hasSurvey: false, isWorking: false, maxRows: 10, bodyColumns: 120, scroll: { offset: 0, bodyRows: 9 }, view: {} },
    })
    expect(await ui.find({ type: 'Text', text: /Último prompt: \$0\.250 · 3 chamadas/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: 'Sessão: $1.25 · contexto 44% · 5h 12.5%' })).toBeDefined()

    await ui.press({ key: 'ocultar' })
    expect(await ui.find({ type: 'Text', text: 'faixa do engine' })).toBeDefined()
    expect(await ui.find({ key: 'ocultar' })).toBeUndefined()

    const shown = await $.command.run({ command: 'creditos' })
    expect(shown).toMatchObject({ text: expect.stringContaining('Consumo da sessão: $1.25') })
    expect(await ui.find({ key: 'ocultar' })).toBeDefined()
    await ui.unmount()
  }
})
