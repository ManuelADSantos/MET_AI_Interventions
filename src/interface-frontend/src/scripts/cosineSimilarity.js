const tokenize = (text) => String(text || '')
  .toLocaleLowerCase('en')
  .match(/[\p{L}\p{N}]+/gu) || []

const termFrequencies = (text) => {
  const frequencies = new Map()
  tokenize(text).forEach((token) => frequencies.set(token, (frequencies.get(token) || 0) + 1))
  return frequencies
}

export const cosineSimilarity = (leftText, rightText) => {
  const left = termFrequencies(leftText)
  const right = termFrequencies(rightText)
  if (!left.size || !right.size) return 0

  let dotProduct = 0
  let leftMagnitude = 0
  let rightMagnitude = 0

  left.forEach((count, token) => {
    dotProduct += count * (right.get(token) || 0)
    leftMagnitude += count * count
  })
  right.forEach((count) => { rightMagnitude += count * count })

  return Math.min(1, dotProduct / (Math.sqrt(leftMagnitude) * Math.sqrt(rightMagnitude)))
}

// The copy blocks are the participant-facing task text intended for reuse:
// the Exercise block contains the question/statements and the Scenario block
// contains the supporting information.
export const getTaskCopyableText = (task) => (task?.tabs || [])
  .map((tab) => tab.copyText)
  .filter(Boolean)
  .join('\n\n')
