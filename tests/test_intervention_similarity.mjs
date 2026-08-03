// The intervention similarity gate (alternatives + pause-points): does 0.25 actually separate
// task prompts from chit-chat?
// Run: docker compose exec frontend node /tests/test_intervention_similarity.mjs

import assert from 'node:assert'
import { readFileSync } from 'node:fs'
import { cosineSimilarity, getTaskCopyableText } from '/app/src/scripts/cosineSimilarity.js'

const THRESHOLD = 0.25 // keep in sync with SIMILARITY_THRESHOLD in ChatView.jsx

// Real task text, not a paraphrase — the threshold is only meaningful against what participants see.
const source = readFileSync('/app/customizations/ai_tasks.md', 'utf8')
const copyBlocks = [...source.matchAll(/:::copy\n([\s\S]*?)\n:::/g)].map((m) => m[1].trim())
assert.ok(copyBlocks.length >= 12, `expected the 12 task copy blocks, found ${copyBlocks.length}`)

// getTaskCopyableText joins the Exercise + Scenario tabs, which is what ChatView compares against
const task = { tabs: [{ copyText: copyBlocks[0] }, { copyText: copyBlocks[1] }] }
const taskText = getTaskCopyableText(task)
assert.ok(taskText.includes(copyBlocks[0]) && taskText.includes(copyBlocks[1]))
assert.strictEqual(getTaskCopyableText({ tabs: [{ copyText: 'a' }, {}, { copyText: 'b' }] }), 'a\n\nb')
assert.strictEqual(getTaskCopyableText(null), '')

const score = (prompt) => cosineSimilarity(prompt, taskText)

// --- engages: the prompt restates the task, which is what the copy button produces ---
assert.ok(score(copyBlocks[0]) >= THRESHOLD, 'pasting the copy block verbatim must engage')
assert.ok(
  score(`Can you help me with this? ${copyBlocks[0]}`) >= THRESHOLD,
  'copy block with a lead-in must engage'
)

// --- does not engage: prompts with nothing of the task in them ---
for (const chitchat of ['hi', 'thanks!', 'are you there?', 'what model are you?', 'how long is this study?']) {
  assert.ok(score(chitchat) < THRESHOLD, `"${chitchat}" must not engage (scored ${score(chitchat)})`)
}

// --- the gap the threshold sits in ---
const onTask = score(copyBlocks[0])
const offTask = Math.max(...['hi', 'thanks!', 'what model are you?'].map(score))
assert.ok(onTask > offTask * 2, `on-task ${onTask.toFixed(3)} should clear off-task ${offTask.toFixed(3)} by a wide margin`)

// --- edge cases the gate must not crash on ---
assert.strictEqual(cosineSimilarity('', taskText), 0)
assert.strictEqual(cosineSimilarity(undefined, undefined), 0)
assert.strictEqual(cosineSimilarity('same words here', 'same words here'), 1)
// case and punctuation are normalised away
assert.strictEqual(cosineSimilarity('Only Statement 1!', 'only statement 1'), 1)

console.log(`intervention similarity gate: all assertions passed (on-task ${onTask.toFixed(3)}, off-task ${offTask.toFixed(3)}, threshold ${THRESHOLD})`)
