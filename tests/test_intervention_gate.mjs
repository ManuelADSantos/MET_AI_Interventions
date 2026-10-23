// The intervention gate (alternatives + pause-points): does the prompt actually carry the task's
// question? Pasting only the scenario must NOT engage — `alternatives` would otherwise argue four
// options over two numbered statements it has never seen, and invent them.
// Run: docker compose exec frontend node /tests/test_intervention_gate.mjs

import assert from 'node:assert'
import { readFileSync } from 'node:fs'
import loadTasks from '/app/src/scripts/taskParser/taskParser.js'
import { questionCoverage, questionTerms, QUESTION_THRESHOLD as THRESHOLD } from '/app/src/scripts/taskQuestion.js'

// Real task text, parsed the way the app parses it — the threshold is only meaningful against what
// participants see. THRESHOLD is taskQuestion.js's default (intervention_similarity_threshold).
const tasks = loadTasks(readFileSync('/app/customizations/ai_tasks.md', 'utf8'), { randomize: false })
  .filter((page) => page.title.startsWith('Scenario:'))
assert.strictEqual(tasks.length, 12, `expected the 12 exercises, found ${tasks.length}`)

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

  // --- does not engage: the scenario pasted alone, and prompts holding nothing of the task ---
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

console.log(`intervention gate: all assertions passed (worst on-task ${worstOnTask.toFixed(3)}, worst off-task ${worstOffTask.toFixed(3)}, threshold ${THRESHOLD})`)
