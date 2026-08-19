// Post-task reflection helper tests.
// Run: docker compose exec frontend node /tests/test_reflection_summary.mjs

import assert from 'node:assert'
import { buildTranscript, contributionStats, coverage, parseSummary, scopeMessages } from '/app/src/scripts/reflectionSummary.js'

// --- parseSummary: bare JSON, the documented happy path ---
const bare = '{"problems":[{"item":"Spotting mutually exclusive constraints","covered":true}],"learning":[{"item":"Boolean logic over two statements","covered":false}]}'
let s = parseSummary(bare)
assert.deepStrictEqual(s.problems, [{ item: 'Spotting mutually exclusive constraints', covered: true }])
assert.deepStrictEqual(s.learning, [{ item: 'Boolean logic over two statements', covered: false }])

// --- parseSummary: fenced, which models do despite being told not to ---
s = parseSummary('```json\n' + bare + '\n```')
assert.strictEqual(s.problems[0].covered, true)
s = parseSummary('Here you go:\n```\n' + bare + '\n```\nHope that helps!')
assert.strictEqual(s.learning[0].covered, false)

// --- parseSummary: prose-wrapped, no fence ---
s = parseSummary('Sure. ' + bare + ' Let me know.')
assert.strictEqual(s.problems.length, 1)

// --- parseSummary: `covered` must be strictly true, never truthy ---
s = parseSummary('{"problems":[{"item":"a","covered":"yes"},{"item":"b","covered":1}],"learning":[]}')
assert.deepStrictEqual(s.problems.map((p) => p.covered), [false, false],
  'only boolean true counts as covered — a truthy string must not inflate the coverage score')

// --- parseSummary: malformed input must throw so the UI shows its fallback ---
for (const bad of ['', 'I cannot help with that.', '{"problems":[]}', '{"problems":[],"learning":[]}', '{oops']) {
  assert.throws(() => parseSummary(bad), `expected throw for ${JSON.stringify(bad)}`)
}
// items without a string `item` are dropped, and dropping everything throws
assert.throws(() => parseSummary('{"problems":[{"covered":true}],"learning":[]}'))

// --- coverage ---
assert.strictEqual(coverage([{ covered: true }, { covered: false }, { covered: true }]), '2/3')
assert.strictEqual(coverage([]), '0/0')

// --- contributionStats: re-prompt = later turn on the same task, or an explicit regenerate ---
const messages = [
  { role: 'user', content: 'help me with task one', task: 5 },
  { role: 'assistant', choices: [{ message: { content: 'Sure, here is A.' } }] },
  { role: 'user', content: 'no try again', task: 5 },                 // 2nd on task 5 -> re-prompt
  { role: 'assistant', choices: [{ message: { content: 'Here is B.' } }] },
  { role: 'user', content: 'now task two', task: 6 },                 // first on task 6 -> not
  { role: 'assistant', choices: [{ message: { content: 'Here is C.' } }] },
  { role: 'user', content: 'again', task: 7, regenerated: true }      // explicit regenerate -> re-prompt
]
const stats = contributionStats(messages)
assert.strictEqual(stats.reprompts, 2, 'two re-prompts: the repeat on task 5 and the regenerate')
assert.strictEqual(stats.aiReplies, 3)
assert.strictEqual(stats.words, 5 + 3 + 3 + 1) // 'help me with task one' + 'no try again' + 'now task two' + 'again'
assert.deepStrictEqual(contributionStats([]), { words: 0, aiReplies: 0, reprompts: 0 })

// --- buildTranscript: both message shapes, newest kept when truncating ---
const t = buildTranscript(messages)
assert.ok(t.includes('USER: help me with task one'))
assert.ok(t.includes('AI: Sure, here is A.'), 'assistant text comes out of choices[0].message.content')
const clipped = buildTranscript(messages, 40)
assert.strictEqual(clipped.length, 40)
assert.ok(t.endsWith(clipped), 'truncation keeps the most recent turns')

// --- scopeMessages: prompts key off `task`, completions off `survey_index` ---
const mixed = [
  { role: 'user', content: 'q6', task: 6 },
  { role: 'assistant', survey_index: 6, choices: [{ message: { content: 'a6' } }] },
  { role: 'user', content: 'q7', task: 7 },
  { role: 'assistant', survey_index: 7, choices: [{ message: { content: 'a7' } }] },
  { role: 'user', content: 'q8', task: 8 },
  { role: 'assistant', survey_index: 8, choices: [{ message: { content: 'a8' } }] }
]
assert.strictEqual(scopeMessages(mixed, null).length, 6, 'null scope = whole study')
assert.strictEqual(scopeMessages(mixed, [7]).length, 2, 'single task keeps its prompt + reply')
assert.deepStrictEqual(scopeMessages(mixed, [7]).map((m) => m.content || m.survey_index), ['q7', 7])
assert.strictEqual(scopeMessages(mixed, [6, 7]).length, 4, 'scenario scope spans several tasks')
assert.strictEqual(scopeMessages(mixed, [99]).length, 0, 'unmatched scope yields nothing')
// a scoped reflection must not see other tasks' work
assert.ok(!buildTranscript(scopeMessages(mixed, [7])).includes('q6'))
assert.strictEqual(contributionStats(scopeMessages(mixed, [7])).aiReplies, 1)

console.log('reflection summary: all assertions passed')
