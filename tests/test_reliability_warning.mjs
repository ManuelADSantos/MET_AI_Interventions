// ai_reliability warning: deterministic sampling + config resolution tests.
// Run: docker compose exec frontend node /tests/test_reliability_warning.mjs

import { sampleN, shuffleWithSeed } from '/app/src/scripts/deterministicRandom.js'
import { resolveReliabilityWarning } from '/app/src/scripts/reliabilityWarning.js'
import assert from 'node:assert'

const pool = ['a', 'b', 'c', 'd', 'e']

// Same seed -> same sample, every time
const first = sampleN(pool, 2, 'participant-1:3')
for (let i = 0; i < 10; i++) {
  assert.deepStrictEqual(sampleN(pool, 2, 'participant-1:3'), first, 'sampling must be deterministic for a fixed seed')
}

// Different participant or task -> sampling is not forced to match
const byParticipant = new Set([
  sampleN(pool, 2, 'participant-1:3').join(','),
  sampleN(pool, 2, 'participant-2:3').join(','),
  sampleN(pool, 2, 'participant-3:3').join(',')
])
assert.ok(byParticipant.size > 1, 'different participants should not always land on the same sample')

const bySourceIndex = new Set([
  sampleN(pool, 2, 'participant-1:3').join(','),
  sampleN(pool, 2, 'participant-1:4').join(','),
  sampleN(pool, 2, 'participant-1:5').join(',')
])
assert.ok(bySourceIndex.size > 1, 'different tasks (sourceIndex) should not always land on the same sample')

// n=0 / empty pool edge cases
assert.deepStrictEqual(sampleN(pool, 0, 'seed'), [])
assert.deepStrictEqual(sampleN([], 3, 'seed'), [])
assert.strictEqual(sampleN(pool, 100, 'seed').length, pool.length, 'sampling more than available clamps to pool size')
assert.deepStrictEqual(shuffleWithSeed(pool, 'seed'), shuffleWithSeed(pool, 'seed'), 'shuffle must be deterministic for a fixed seed')
assert.deepStrictEqual(shuffleWithSeed([], 'seed'), [], 'shuffle handles empty lists')

// resolveReliabilityWarning: fixed entries first, then sampled pool
const config = {
  tasks: {
    3: {
      show: true,
      reliability: { label: 'Low', color: '#ef4444', markerValue: 20, explanatoryText: 'text' },
      strategies: {
        heading: 'Beware of AI ...',
        fixed: [{ title: 'fixed-1', description: '...' }, { title: 'fixed-2', description: '...' }],
        pool: [{ title: 'pool-1', description: '...' }, { title: 'pool-2', description: '...' }, { title: 'pool-3', description: '...' }],
        poolSampleSize: 1
      }
    },
    4: { show: false, reliability: {}, strategies: { fixed: [], pool: [] } }
  }
}

const resolved = resolveReliabilityWarning(config, 3, 'participant-1')
assert.strictEqual(resolved.entries.length, 3, 'expected 2 fixed + 1 sampled pool entry')
assert.deepStrictEqual(resolved.entries.slice(0, 2), config.tasks[3].strategies.fixed, 'fixed entries must come first, in authored order')
assert.ok(config.tasks[3].strategies.pool.some((p) => p.title === resolved.entries[2].title), 'third entry must come from the pool')

const randomizedConfig = {
  randomizeStrategyOrder: true,
  tasks: config.tasks
}
const randomized = resolveReliabilityWarning(randomizedConfig, 3, 'participant-1')
assert.deepStrictEqual(
  randomized,
  resolveReliabilityWarning(randomizedConfig, 3, 'participant-1'),
  'randomized strategy order must stay stable for the same participant + task'
)
assert.deepStrictEqual(
  randomized.entries.map((entry) => entry.title).sort(),
  resolved.entries.map((entry) => entry.title).sort(),
  'randomized strategy order must keep the same selected entries'
)

// Determinism carries through the resolver too
assert.deepStrictEqual(
  resolveReliabilityWarning(config, 3, 'participant-1'),
  resolveReliabilityWarning(config, 3, 'participant-1'),
  'resolving the same task for the same participant must be stable across calls (e.g. reshuffled task order)'
)

// show:false and missing task both hide the warning
assert.strictEqual(resolveReliabilityWarning(config, 4, 'participant-1'), null, 'show:false must hide the warning')
assert.strictEqual(resolveReliabilityWarning(config, 999, 'participant-1'), null, 'missing task config must hide the warning')

console.log('test_reliability_warning.mjs: all assertions passed')
