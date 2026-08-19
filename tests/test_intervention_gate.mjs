// The intervention gate (alternatives + pause-points): does the prompt actually carry the task's
// question? Pasting only the scenario must NOT engage — `alternatives` would otherwise argue four
// options over two numbered statements it has never seen, and invent them.
// Run: docker compose exec frontend node /tests/test_intervention_gate.mjs

import assert from 'node:assert'
import { readFileSync } from 'node:fs'
import { questionCoverage, questionTerms } from '/app/src/scripts/taskQuestion.js'

const THRESHOLD = 0.6 // keep in sync with QUESTION_THRESHOLD in ChatView.jsx

// Real task text, not a paraphrase — the threshold is only meaningful against what participants see.
const source = readFileSync('/app/customizations/ai_tasks.md', 'utf8')
const tabs = [...source.matchAll(/:::tab\s+(\w+)\n([\s\S]*?)(?=:::tab|\n# |$)/g)]
  .map(([, title, body]) => ({ title, copyText: (body.match(/:::copy\n([\s\S]*?)\n:::/) || [, ''])[1].trim() }))
  .filter((tab) => tab.copyText)
const tasks = []
for (let i = 0; i < tabs.length - 1; i++) {
  if (tabs[i].title === 'Exercise' && tabs[i + 1].title === 'Scenario') tasks.push({ tabs: [tabs[i], tabs[i + 1]] })
}
assert.ok(tasks.length >= 12, `expected the 12 Exercise+Scenario tasks, found ${tasks.length}`)

let worstOnTask = 1
let worstOffTask = 0

for (const task of tasks) {
  const terms = questionTerms(task)
  assert.ok(terms.length >= 5, `question signature too thin: ${terms.join(' ')}`)

  const [exercise, scenario] = task.tabs.map((tab) => tab.copyText)
  const wholeTask = `${exercise}\n\n${scenario}`
  const score = (prompt) => questionCoverage(prompt, terms)

  // --- engages: the prompt carries the question, which is what the copy button produces ---
  for (const onTask of [exercise, wholeTask, `Can you help me with this? ${wholeTask}`, `${wholeTask}\n\nWhich option is right?`]) {
    assert.ok(score(onTask) >= THRESHOLD, `on-task prompt must engage (scored ${score(onTask).toFixed(3)})`)
    worstOnTask = Math.min(worstOnTask, score(onTask))
  }

  // --- does not engage: the reported bug (scenario only) plus prompts holding nothing of the task ---
  for (const offTask of [scenario, `Can you help me with this? ${scenario}`, 'hi', 'thanks!', 'what model are you?', 'which option should i pick?']) {
    assert.ok(score(offTask) < THRESHOLD, `off-task prompt must not engage (scored ${score(offTask).toFixed(3)})`)
    worstOffTask = Math.max(worstOffTask, score(offTask))
  }
}

// --- the gap the threshold sits in ---
assert.ok(worstOnTask - worstOffTask > 0.3, `margin too thin: on-task ${worstOnTask}, off-task ${worstOffTask}`)

// --- edge cases the gate must not crash on ---
assert.deepStrictEqual(questionTerms(null), [])
assert.deepStrictEqual(questionTerms({ tabs: [] }), [])
assert.strictEqual(questionCoverage('anything', []), 0) // no question text -> never engages
assert.strictEqual(questionCoverage('', ['statement']), 0)
assert.strictEqual(questionCoverage(undefined, ['statement']), 0)
// a single-tab page has no scenario to subtract, so the whole block is the signature
assert.deepStrictEqual(questionTerms({ tabs: [{ copyText: 'Only statement 1' }] }), ['only', 'statement', '1'])
// case and punctuation are normalised away
assert.strictEqual(questionCoverage('Only Statement 1!', ['only', 'statement', '1']), 1)

console.log(`intervention gate: all assertions passed (worst on-task ${worstOnTask.toFixed(3)}, worst off-task ${worstOffTask.toFixed(3)}, threshold ${THRESHOLD})`)
