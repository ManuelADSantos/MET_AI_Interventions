const baseURL = import.meta.env.VITE_PROXY_URL || `http://${window.location.hostname}:5001`
const SYSTEM_PROMPT = import.meta.env.VITE_SYSTEM_PROMPT || ''

/**
 * Request a chat completion based on a list of messages from oldest to newest
 *
 * @param {Array} messages The list of chat messages so far. Should include at least one message (prompt from user).
 * @returns The full API response containing the chat completion
 */
const requestChatResponse = async (messages, signal) => {
  try {
    const messagesToSend = messages.filter((m) => ['user', 'assistant'].includes(m.role))
    if (SYSTEM_PROMPT) {
      messagesToSend.unshift({ role: 'system', content: SYSTEM_PROMPT })
    }
    const res = await fetch(`${baseURL}/chat`, {
      method: 'POST',
      signal,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: messagesToSend
      })
    })

    const parsed = await res.json()

    if (parsed.error) {
      throw new Error(parsed.error)
    }

    return parsed.response
  } catch (e) {
    return { error: e.message }
  }
}

const requestChatResponseStream = async function* (messages, signal) {
  const messagesToSend = messages.filter((m) => ['user', 'assistant'].includes(m.role))
  if (SYSTEM_PROMPT) {
    messagesToSend.unshift({ role: 'system', content: SYSTEM_PROMPT })
  }

  const res = await fetch(`${baseURL}/chat/stream`, {
    method: 'POST',
    signal,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages: messagesToSend
    })
  })

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

export { requestChatResponse, requestChatResponseStream }
