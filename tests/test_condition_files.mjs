// The AI-arm condition files are full copies of ai_tasks.md rather than symlinks, so each condition
// can ask different post-questionnaire questions. That makes drift possible: everything BEFORE the
// first "# Post-Questionnaire" page is the shared stimulus and must stay byte-identical across arms,
// because a stray edit in one file is a confound. Everything after it is free to differ.
// Run: docker compose exec frontend node /tests/test_condition_files.mjs

import assert from 'node:assert'
import { lstatSync, readdirSync, readFileSync } from 'node:fs'

const DIR = '/app/customizations'
const SPLIT = '\n# Post-Questionnaire'
const REFERENCE = 'ai_tasks.md'
// no_ai is separately authored, not a copy: American spelling throughout and the consultant
// availability as a table rather than a list. Checked for structure only.
const SEPARATE = new Set(['no_ai_tasks.md'])

const files = readdirSync(DIR).filter((f) => f.endsWith('_tasks.md')).sort()
assert.ok(files.includes(REFERENCE), `${REFERENCE} missing`)

const stimulus = (name) => {
  const raw = readFileSync(`${DIR}/${name}`, 'utf8')
  const cut = raw.indexOf(SPLIT)
  assert.notStrictEqual(cut, -1, `${name}: no "# Post-Questionnaire" page to split on`)
  return raw.slice(0, cut)
}

const reference = stimulus(REFERENCE)
const copies = files.filter((f) => f !== REFERENCE && !SEPARATE.has(f))
assert.ok(copies.length >= 4, `expected the AI-arm copies, found ${copies.length}: ${copies}`)

for (const name of copies) {
  // A symlink would defeat the point of splitting these files in the first place
  assert.ok(!lstatSync(`${DIR}/${name}`).isSymbolicLink(), `${name} is a symlink again`)
  assert.strictEqual(
    stimulus(name), reference,
    `${name}: task text drifted from ${REFERENCE} before the questionnaire`
  )
}

// Whatever a file's questionnaire asks, the stimulus set itself must be intact
for (const name of files) {
  const raw = readFileSync(`${DIR}/${name}`, 'utf8')
  assert.strictEqual((raw.match(/^# Scenario:/gm) || []).length, 12, `${name}: not 12 scenario pages`)
  assert.strictEqual((raw.match(/:::copy/g) || []).length, 26, `${name}: copy-block count changed`)
}

const questions = (name) => (readFileSync(`${DIR}/${name}`, 'utf8').split(SPLIT).slice(1).join('\n').match(/^>/gm) || []).length
console.log(`condition files: ${copies.length} copies match ${REFERENCE} before the questionnaire; all ${files.length} have 12 scenarios`)
console.log(`questionnaire lines per condition: ${files.map((f) => `${f.replace('_tasks.md', '')}=${questions(f)}`).join(' ')}`)
