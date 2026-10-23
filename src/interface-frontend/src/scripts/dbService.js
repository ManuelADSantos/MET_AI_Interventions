const baseURL = import.meta.env.VITE_PROXY_URL || `http://${window.location.hostname}:5001`

const saveToDatabase = async (data) => {
  try {
    // ponytail: 60s timeout — Railway's gateway times out at 30s on free/starter, returning HTML
    // that res.json() can't parse, hanging the spinner forever. The AbortSignal ensures the fetch
    // rejects cleanly so the retry button appears.
    const res = await fetch(`${baseURL}/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data),
      signal: AbortSignal.timeout(60_000)
    })

    if (!res.ok) {
      const errorBody = await res.json().catch(() => null)
      throw new Error(errorBody?.error || 'Failed to save data. Please try again.')
    }

    const response = await res.json()

    return response
  } catch (e) {
    if (e.name === 'TimeoutError') return { error: 'The request timed out. Please click "Try again".' }
    return {'error': e.message}
  }
}

const checkParticipation = async (id) => {
  try {
    const res = await fetch(`${baseURL}/check_participation`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }, 
      body: JSON.stringify({id: String(id)})
    })

    if (!res.ok) {
      throw new Error('Something went wrong. Please try again.')
    }

    const body = await res.json()
    return body.participated
      ? {'error': 'Participation with given ID already registered.'}
      : {}
  } catch (e) {
    return {'error': e.message}
  }
}

export {saveToDatabase, checkParticipation}