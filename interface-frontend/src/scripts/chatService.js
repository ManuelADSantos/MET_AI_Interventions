const baseURL = import.meta.env.VITE_PROXY_URL || `http://${window.location.hostname}:5001`
const SYSTEM_PROMPT = import.meta.env.VITE_SYSTEM_PROMPT || ''

/**
 * Mint a per-participant chat token from the backend and cache it in sessionStorage.
 * Reads the pid/condition stored by App.jsx at study start.
 */
const mintChatToken = async () => {
  const id = sessionStorage.getItem('pid')
  const condition = sessionStorage.getItem('condition')
  if (!id || !condition) throw new Error('No active session — reload and enter your participant ID')
  const payload = { id, condition }
  const res = await fetch(`${baseURL}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!res.ok) {
    console.error('[mintChatToken] 400 payload:', payload, 'url:', `${baseURL}/token`)
    throw new Error(`Token request failed with status ${res.status}`)
  }
  const token = (await res.json()).token
  sessionStorage.setItem('chatToken', token)
  return token
}

/**
 * Request a chat completion based on a list of messages from oldest to newest
 *
 * @param {Array} messages The list of chat messages so far. Should include at least one message (prompt from user).
 * @returns The full API response containing the chat completion
 */
const requestChatResponseStream = async function* (messages, signal, taskSimilar = false) {
  const messagesToSend = messages.filter((m) => ['user', 'assistant'].includes(m.role))
  if (SYSTEM_PROMPT) {
    messagesToSend.unshift({ role: 'system', content: SYSTEM_PROMPT })
  }

  const send = (token) => fetch(`${baseURL}/chat/stream`, {
    method: 'POST',
    signal,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      messages: messagesToSend,
      // Gates the intervention system prompt server-side (see app.py stream_message)
      taskSimilar
    })
  })

  let res = await send(sessionStorage.getItem('chatToken') || await mintChatToken())
  if (res.status === 401) {
    // Token unknown to the server (e.g. backend redeploy) — re-mint once and retry
    res = await send(await mintChatToken())
  }

  if (!res.ok || !res.body) {
    let errorMessage = `Streaming request failed with status ${res.status}`
    try {
      const parsed = await res.json()
      errorMessage = parsed.error || errorMessage
    } catch (_) {}
    throw new Error(errorMessage)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.trim()) continue

      const event = JSON.parse(line)
      if (event.type === 'error') {
        throw new Error(event.error)
      }

      yield event
    }
  }

  const finalLine = buffer.trim()
  if (finalLine) {
    const event = JSON.parse(finalLine)
    if (event.type === 'error') {
      throw new Error(event.error)
    }
    yield event
  }
}

export { requestChatResponseStream, mintChatToken }
