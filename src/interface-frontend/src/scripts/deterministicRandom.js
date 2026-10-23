/** Small deterministic string hash (cyrb53-style) used to seed the PRNG below. */
const hashString = (str) => {
  let h1 = 0xdeadbeef
  let h2 = 0x41c6ce57

  for (let i = 0; i < str.length; i++) {
    const ch = str.charCodeAt(i)
    h1 = Math.imul(h1 ^ ch, 2654435761)
    h2 = Math.imul(h2 ^ ch, 1597334677)
  }

  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909)
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909)

  return (h1 >>> 0) ^ (h2 >>> 0)
}

/** mulberry32: small, fast seeded PRNG returning a () => [0, 1) generator. */
const mulberry32 = (seed) => {
  let state = seed >>> 0

  return () => {
    state |= 0
    state = (state + 0x6d2b79f5) | 0
    let t = Math.imul(state ^ (state >>> 15), 1 | state)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/** Deterministically shuffles `items` from `seedString`. Same seed always
 * yields the same result, independent of external randomization. */
const shuffleWithSeed = (items, seedString) => {
  const random = mulberry32(hashString(seedString))
  const shuffled = [...items]

  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }

  return shuffled
}

/** Deterministically picks the first `n` items of `items` after seeding a
 * Fisher-Yates shuffle from `seedString`. Same seed always yields the same
 * result, independent of any external randomization (e.g. task order). */
const sampleN = (items, n, seedString) => {
  const count = Math.max(0, Math.min(n, items.length))
  if (count === 0) return []

  const shuffled = shuffleWithSeed(items, seedString)
  return shuffled.slice(0, count)
}

export { hashString, mulberry32, sampleN, shuffleWithSeed }
