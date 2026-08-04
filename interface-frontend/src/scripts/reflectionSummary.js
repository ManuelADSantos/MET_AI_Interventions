/** Pure helpers for the post-task reflection review (ReflectionSummary.jsx).
 * Kept out of the component so they can be asserted by tests/test_reflection_summary.mjs. */

// /chat/stream rejects above 200k chars; stay well clear and keep the most recent turns
const MAX_TRANSCRIPT_CHARS = 60_000

const assistantText = (m) => m.choices?.[0]?.message?.content || m.content || ''

/** Narrow the transcript to one task or one scenario. Prompts carry `task`, completions
 * carry `survey_index` (see ChatView). `ids = null` means the whole study. */
export const scopeMessages = (messages, ids) => {
  if (!ids) return messages
  const wanted = new Set(ids)
  return messages.filter((m) => wanted.has(m.role === 'user' ? m.task : m.survey_index))
}

/** Flatten store.messages (user prompts + raw completion objects) into a plain transcript. */
export const buildTranscript = (messages, limit = MAX_TRANSCRIPT_CHARS) => {
  const text = messages
    .map((m) => (m.role === 'user' ? `USER: ${m.content || ''}` : `AI: ${assistantText(m)}`))
    .filter((line) => line.length > 6)
    .join('\n\n')
  return text.length > limit ? text.slice(-limit) : text
}

/** The reviewer is told to return bare minified JSON, but models still fence it sometimes.
 * Throws on anything that isn't the expected shape so the caller shows its fallback. */
export const parseSummary = (raw) => {
  const text = String(raw || '').trim()
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/)
  const body = (fenced ? fenced[1] : text).trim()
  // ponytail: models occasionally wrap the object in prose — take the outermost braces
  const start = body.indexOf('{')
  const end = body.lastIndexOf('}')
  if (start === -1 || end <= start) throw new Error('no JSON object in reviewer reply')
  const parsed = JSON.parse(body.slice(start, end + 1))
  const list = (v) => (Array.isArray(v) ? v : []).filter((x) => x && typeof x.item === 'string')
  const problems = list(parsed.problems)
  const learning = list(parsed.learning)
  if (!problems.length && !learning.length) throw new Error('reviewer reply had no items')
  return {
    problems: problems.map((p) => ({ item: p.item, covered: p.covered === true })),
    learning: learning.map((p) => ({ item: p.item, covered: p.covered === true }))
  }
}

/** "Where the work came from" — plain arithmetic over the log, no LLM needed.
 * A re-prompt is any user turn after the first on a given task, plus explicit regenerations. */
export const contributionStats = (messages) => {
  const userMessages = messages.filter((m) => m.role === 'user')
  const words = userMessages.reduce(
    (n, m) => n + String(m.content || '').trim().split(/\s+/).filter(Boolean).length, 0
  )
  const seen = new Set()
  const reprompts = userMessages.filter((m) => {
    if (m.regenerated) return true
    if (seen.has(m.task)) return true
    seen.add(m.task)
    return false
  }).length
  return {
    words,
    aiReplies: messages.filter((m) => m.role === 'assistant').length,
    reprompts
  }
}

export const coverage = (items) => `${items.filter((i) => i.covered).length}/${items.length}`
