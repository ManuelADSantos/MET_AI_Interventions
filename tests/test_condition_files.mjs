// The AI-arm condition files are full copies of ai_tasks.md rather than symlinks, so each condition
// can add its own reflection pages and ask different post-questionnaire questions. That makes drift
// possible, so the 12 "# Scenario: ..." pages — the actual stimulus — must stay byte-identical across
// arms; a stray edit to one of them in one file is a confound. Everything else is free to differ.
// Run: docker compose exec frontend node /tests/test_condition_files.mjs

import assert from 'node:assert'
import { lstatSync, readdirSync, readFileSync } from 'node:fs'
import loadTasks from '/app/src/scripts/taskParser/taskParser.js'

const DIR = '/app/customizations'
const REFERENCE = 'ai_tasks.md'
// no_ai is separately authored, not a copy: American spelling throughout and the consultant
// availability as a table rather than a list. Checked for structure only.
const SEPARATE = new Set(['no_ai_tasks.md'])

const reflections = (name) => (readFileSync(`${DIR}/${name}`, 'utf8').match(/:::reflect-summary/g) || []).length
const scopeSizes = {}

const files = readdirSync(DIR).filter((f) => f.endsWith('_tasks.md')).sort()
assert.ok(files.includes(REFERENCE), `${REFERENCE} missing`)

const scenarioPages = (name) => readFileSync(`${DIR}/${name}`, 'utf8')
  .split(/^(?=# )/m)
  .filter((page) => page.startsWith('# Scenario: '))
  // a reflection page inserted after a task is part of the next chunk's split, so cut at any %%
  .map((page) => page.split('\n%%')[0].split('\n# ')[0].trimEnd())

const reference = scenarioPages(REFERENCE)
assert.strictEqual(reference.length, 12, `${REFERENCE}: expected 12 scenario pages, got ${reference.length}`)

const copies = files.filter((f) => f !== REFERENCE && !SEPARATE.has(f))
assert.ok(copies.length >= 4, `expected the AI-arm copies, found ${copies.length}: ${copies}`)

for (const name of copies) {
  // A symlink would defeat the point of splitting these files in the first place
  assert.ok(!lstatSync(`${DIR}/${name}`).isSymbolicLink(), `${name} is a symlink again`)
  const pages = scenarioPages(name)
  assert.strictEqual(pages.length, 12, `${name}: expected 12 scenario pages, got ${pages.length}`)
  pages.forEach((page, i) => assert.strictEqual(
    page, reference[i],
    `${name}: scenario page ${i + 1} drifted from ${REFERENCE}`
  ))
}

// Reflection pages must carry the questions their review depends on, or the summary has nothing to judge
for (const name of files) {
  const raw = readFileSync(`${DIR}/${name}`, 'utf8')
  const reflect = raw.split(/^(?=# )/m).filter((p) => p.includes(':::reflect-summary'))
  for (const page of reflect) {
    assert.ok(/\$textarea;\s*\d+/.test(page), `${name}: a :::reflect-summary page has no minimum-length textarea`)
  }
}

// What a reflection reviews is the unbroken run of chat pages in front of it (scopeIds in TaskView).
// Parse for real, with randomization, and check no scope ever reaches a page that is not one of the 12
// exercises — the trial has chat too, and only the chat-less "# Main Tasks" divider keeps it out.
const scopeIds = (pages, i) => {
  const ids = []
  for (let k = i - 1; k >= 0 && pages[k].chatEnabled; k -= 1) ids.push(pages[k].sourceIndex)
  return ids
}
for (const name of files.filter((f) => reflections(f) > 0)) {
  const raw = readFileSync(`${DIR}/${name}`, 'utf8')
  const sizes = new Set()
  for (let run = 0; run < 50; run += 1) {
    const pages = loadTasks(raw, { randomize: true })
    pages.forEach((page, i) => {
      if (!page.reflectSummary) return
      const previous = pages[i - 1]
      assert.ok(previous?.title.startsWith('Scenario: '), `${name}: a reflection page is not directly after an exercise`)
      const scope = scopeIds(pages, i)
      assert.ok(scope.length > 0, `${name}: a reflection reviews nothing`)
      for (const id of scope) {
        const title = pages.find((p) => p.sourceIndex === id)?.title || ''
        assert.ok(title.startsWith('Scenario: '), `${name}: a reflection scope reaches "${title}" — expected only exercises`)
      }
      sizes.add(scope.length)
    })
  }
  assert.strictEqual(sizes.size, 1, `${name}: reflection scope size varies with randomization: ${[...sizes]}`)
  scopeSizes[name.replace('_tasks.md', '')] = [...sizes][0]
}

// Whatever a file's questionnaire asks, the stimulus set itself must be intact
for (const name of files) {
  const raw = readFileSync(`${DIR}/${name}`, 'utf8')
  assert.strictEqual((raw.match(/^# Scenario:/gm) || []).length, 12, `${name}: not 12 scenario pages`)
  assert.strictEqual((raw.match(/:::copy/g) || []).length, 26, `${name}: copy-block count changed`)
}

console.log(`condition files: the 12 scenario pages are identical across ${copies.length} copies of ${REFERENCE}`)
console.log(`reflection pages: ${files.map((f) => `${f.replace('_tasks.md', '')}=${reflections(f)}`).join(' ')}`)
console.log(`tasks reviewed per reflection: ${Object.entries(scopeSizes).map(([k, v]) => `${k}=${v}`).join(' ')}`)
