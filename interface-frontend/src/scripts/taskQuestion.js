const tokenize = (text) => String(text || '')
  .toLocaleLowerCase('en')
  .match(/[\p{L}\p{N}]+/gu) || []

// The first tab's copy block is the Exercise (the question plus its two numbered statements); the
// remaining tabs hold the scenario, which the four tasks of a block share. Terms unique to the
// Exercise are the question's signature, so a prompt that pasted only the scenario scores 0.
export const questionTerms = (task) => {
  const copyBlocks = (task?.tabs || []).map((tab) => tab.copyText).filter(Boolean)
  if (!copyBlocks.length) return []
  const scenarioTerms = new Set(tokenize(copyBlocks.slice(1).join('\n')))
  return [...new Set(tokenize(copyBlocks[0]))].filter((term) => !scenarioTerms.has(term))
}

// ponytail: coverage (recall of the question's terms), not cosine similarity. Cosine is
// length-sensitive, so across the 12 tasks a paste that DOES contain the question scored 0.40-0.71
// against the question text while the scenario alone scored 0.53-0.70 — overlapping bands, no
// threshold could separate them. Coverage is 1.000 for every on-task paste and <=0.118 for
// scenario-only pastes and chit-chat. Upgrade path if participants start retyping the question
// instead of using the copy button: stem the terms, or weight them by inverse document frequency.
export const questionCoverage = (prompt, terms) => {
  if (!terms.length) return 0
  const promptTerms = new Set(tokenize(prompt))
  return terms.filter((term) => promptTerms.has(term)).length / terms.length
}
