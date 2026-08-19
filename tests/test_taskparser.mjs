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

// Structure: intro fixed, all pages present, sourceIndex preserved
const pages = loadTasks(md)
assert.strictEqual(pages.length, 5, `expected 5 pages, got ${pages.length}`)
assert.strictEqual(pages[0].title, 'Introduction', 'intro must stay first')
assert.deepStrictEqual(titles(pages).sort(), ['A1', 'A2', 'B1', 'B2', 'Introduction'].sort())
assert.deepStrictEqual(pages.map((p) => p.sourceIndex).sort((a, b) => a - b), [0, 1, 2, 3, 4], 'sourceIndex must map to source order')

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

// Question directives: optional '?', number min/max, slider tooltip param
const qMd = `# Q

> Optional feedback:

    $textarea?

> Count:

    $number; 5; 42

> Just a number:

    $number

> Rate:

    $slider; 0; 100; Low; High; tooltip%
`
const qItems = loadTasks(qMd)[0].content
const [optional, bounded, plainNumber, slider] = qItems.filter((c) => c.type !== 'paragraph')
assert.strictEqual(optional.required, false, 'trailing ? must mark question optional')
assert.strictEqual(optional.type, 'textarea')
assert.strictEqual(bounded.required, true)
assert.deepStrictEqual([bounded.min, bounded.max], [5, 42], 'number must take custom min/max')
assert.deepStrictEqual([plainNumber.min, plainNumber.max], [0, 999], 'number defaults to 0-999')
assert.deepStrictEqual(slider.additionalParams, ['tooltip%'], 'extra slider params must be preserved')

assert.deepStrictEqual([optional.minChars, optional.maxChars], [2, 400], 'textarea defaults to 2-400 chars')

// --- reflection pages: glued to the task in front of them, and scoped to it ---
// A reflection asks the participant to recall the task above it, so randomization must never
// separate the pair, and the review must never reach back into the trial or an earlier task.
const reflectMd = `# Trial: practice

:::chat-enabled

> Practice.

# Main Tasks

> A divider without chat. It is what stops a reflection scope from reaching back into the trial,
> so every condition file needs one between the trial and the exercises.

%% RANDOMIZE

# Scenario: A

:::chat-enabled

> Task A.

# Pause and reflect

> Explain back:

    $textarea; 200; 4000

:::reflect-summary

# Scenario: B

:::chat-enabled

> Task B.

# Pause and reflect

> Explain back:

    $textarea; 200; 4000

:::reflect-summary
%%
`
// same rule as scopeIds in TaskView
const scopeIds = (pages, i) => {
  const ids = []
  for (let k = i - 1; k >= 0 && pages[k].chatEnabled; k -= 1) ids.push(pages[k].sourceIndex)
  return ids
}
for (let run = 0; run < 200; run += 1) {
  const pages = loadTasks(reflectMd, { randomize: true })
  assert.strictEqual(pages.filter((p) => p.reflectSummary).length, 2)
  pages.forEach((page, i) => {
    if (!page.reflectSummary) return
    const previous = pages[i - 1]
    assert.ok(previous && !previous.reflectSummary && previous.title.startsWith('Scenario:'),
      'a reflection page must stay directly after its own task')
    const scope = scopeIds(pages, i)
    assert.deepStrictEqual(scope, [previous.sourceIndex],
      'a reflection must review only its own task — not the trial, not an earlier task')
  })
}
assert.strictEqual(loadTasks(reflectMd)[0].reflectSummary, false,
  'a page without the directive must not be marked as a reflection')

console.log('All taskParser randomization tests passed.')
