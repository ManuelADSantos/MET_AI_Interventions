// ponytail: one implementation for every copy button in the study (task text, completion code,
// Prolific ID). navigator.clipboard is absent outside secure contexts and Chrome rejects it on a
// site-permission denial, so the synchronous selection fallback has to stay. Returns success —
// a participant who cannot copy the completion code cannot get paid, so callers surface failure.
export const copyToClipboard = async (text) => {
  if (window.isSecureContext && navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch { /* fall through to the selection-based fallback */ }
  }

  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', '')
  textarea.style.cssText = 'position:fixed;opacity:0;pointer-events:none'
  document.body.appendChild(textarea)
  textarea.select()
  textarea.setSelectionRange(0, textarea.value.length)

  try {
    return document.execCommand('copy')
  } catch {
    return false
  } finally {
    textarea.remove()
  }
}

export const cn = (...inputs) => {
  return inputs
    .flatMap((input) => {
      if (!input) return []
      if (typeof input === 'string') return [input]
      if (Array.isArray(input)) return [cn(...input)]
      if (typeof input === 'object') {
        return Object.entries(input)
          .filter(([, value]) => Boolean(value))
          .map(([key]) => key)
      }
      return []
    })
    .filter(Boolean)
    .join(' ')
}
