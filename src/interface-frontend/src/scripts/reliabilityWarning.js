import { sampleN, shuffleWithSeed } from './deterministicRandom.js'

/** Resolves the ai_reliability warning content for a given task, keyed by its
 * stable sourceIndex (not display position), with pool entries deterministically
 * sampled per participant + task so they stay stable across randomized reloads. */
const resolveReliabilityWarning = (config, sourceIndex, participantId) => {
  const taskConfig = config?.tasks?.[String(sourceIndex)]

  if (!taskConfig || taskConfig.show === false) {
    return null
  }

  const strategies = taskConfig.strategies || {}
  const fixed = strategies.fixed || []
  const pool = strategies.pool || []
  const poolSampleSize = strategies.poolSampleSize ?? 0
  const randomizeOrder = strategies.randomizeOrder ?? config?.randomizeStrategyOrder ?? false
  const sampledPool = sampleN(pool, poolSampleSize, `${participantId}:${sourceIndex}`)
  const entries = [...fixed, ...sampledPool]

  return {
    reliability: taskConfig.reliability,
    heading: strategies.heading,
    entries: randomizeOrder
      ? shuffleWithSeed(entries, `${participantId}:${sourceIndex}:strategy-order`)
      : entries
  }
}

export { resolveReliabilityWarning }
