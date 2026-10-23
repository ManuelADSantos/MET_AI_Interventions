// Each condition has its own copy of ai_tasks.md, so it can add its own pages (reflection-task) and
// post-questionnaire questions. That makes drift possible, so the 12 "# Scenario: ..." pages — the
// actual stimulus — must stay byte-identical across conditions; a stray edit to one of them in one
// file is a confound. Everything else is free to differ.
// Run: docker compose exec frontend node /tests/test_condition_files.mjs

import assert from 'node:assert'
import { readdirSync, readFileSync } from 'node:fs'

const DIR = '/app/customizations'
const REFERENCE = 'ai_tasks.md'

const files = readdirSync(DIR).filter((f) => f.endsWith('_tasks.md')).sort()
assert.ok(files.includes(REFERENCE), `${REFERENCE} missing`)

const scenarioPages = (name) => readFileSync(`${DIR}/${name}`, 'utf8')
  .split(/^(?=# )/m)
  .filter((page) => page.startsWith('# Scenario: '))
  // the last scenario page of a block carries the block's closing %% in ai_tasks.md, but is followed by a
  // "# Pause and reflect" page in reflection_task_tasks.md — cut at %% so both compare equal
  .map((page) => page.split('\n%%')[0].trimEnd())

const reference = scenarioPages(REFERENCE)
assert.strictEqual(reference.length, 12, `${REFERENCE}: expected 12 scenario pages, got ${reference.length}`)

const copies = files.filter((f) => f !== REFERENCE)
assert.ok(copies.length >= 4, `expected the AI-arm copies, found ${copies.length}: ${copies}`)

for (const name of copies) {
  const pages = scenarioPages(name)
  assert.strictEqual(pages.length, 12, `${name}: expected 12 scenario pages, got ${pages.length}`)
  pages.forEach((page, i) => assert.strictEqual(
    page, reference[i],
    `${name}: scenario page ${i + 1} drifted from ${REFERENCE}`
  ))
}

// No copy block added to or lost from any other page (trial, reflection, questionnaire)
for (const name of files) {
  const raw = readFileSync(`${DIR}/${name}`, 'utf8')
  assert.strictEqual((raw.match(/:::copy/g) || []).length, 26, `${name}: copy-block count changed`)
}

console.log(`condition files: the 12 scenario pages are identical across ${copies.length} copies of ${REFERENCE}`)
