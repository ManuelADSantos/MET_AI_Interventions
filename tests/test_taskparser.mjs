// Task parser randomization test.
// Run: docker compose exec frontend node /tests/test_taskparser.mjs

import loadTasks from '/app/src/scripts/taskParser/taskParser.js'
import assert from 'node:assert'

const md = `# Introduction

> Welcome text.

%% RANDOMIZE_SECTIONS

%% RANDOMIZE

# A1

> Task A1.

# A2

> Task A2.

%%

%% SECTION

# B1

> Task B1.

# B2

> Task B2.

%%
`

const titles = (pages) => pages.map((p) => p.title)

// Structure: intro fixed, all pages present, and every page keeps its source position as sourceIndex
// after shuffling — answers, scoring and reliability cards are all keyed by it
const SOURCE_ORDER = ['Introduction', 'A1', 'A2', 'B1', 'B2']
for (let i = 0; i < 20; i++) {
  const pages = loadTasks(md)
  assert.strictEqual(pages.length, 5, `expected 5 pages, got ${pages.length}`)
  assert.strictEqual(pages[0].title, 'Introduction', 'intro must stay first')
  assert.deepStrictEqual(titles(pages).sort(), [...SOURCE_ORDER].sort())
  pages.forEach((p) => assert.strictEqual(p.sourceIndex, SOURCE_ORDER.indexOf(p.title), `${p.title}: sourceIndex must be its source position`))
}

// SECTION block keeps internal page order even when sections shuffle
for (let i = 0; i < 20; i++) {
  const t = titles(loadTasks(md))
  assert.ok(t.indexOf('B1') < t.indexOf('B2'), 'SECTION pages must keep order')
}

// Randomization actually happens (P(no shuffle in 50 runs) ~ (1/4)^50)
const orders = new Set(Array.from({ length: 50 }, () => titles(loadTasks(md)).join(',')))
assert.ok(orders.size > 1, 'expected at least two distinct orders across 50 runs')

// Without RANDOMIZE_SECTIONS the source section order is kept
const fixedMd = md.replace('%% RANDOMIZE_SECTIONS\n', '')
for (let i = 0; i < 20; i++) {
  const t = titles(loadTasks(fixedMd))
  const lastA = Math.max(t.indexOf('A1'), t.indexOf('A2'))
  const firstB = Math.min(t.indexOf('B1'), t.indexOf('B2'))
  assert.ok(lastA < firstB, 'sections must not move without the directive')
}

console.log('All taskParser randomization tests passed.')
