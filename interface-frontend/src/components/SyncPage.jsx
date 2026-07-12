import { useState } from 'react'
import { Button, Card, CardBody, Input } from '@nextui-org/react'
import App from '../App'
import { tasksPerCondition } from '../scripts/conditions'

const baseURL = import.meta.env.VITE_PROXY_URL || ''

export default function SyncPage() {
  const [pid, setPid] = useState('')
  const [condition, setCondition] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSync = async (e) => {
    e.preventDefault()
    const trimmedPid = pid.trim()
    if (!trimmedPid) return

    setLoading(true)
    setError('')

    try {
      const res = await fetch(`${baseURL}/api/launch/session/${encodeURIComponent(trimmedPid)}`)
      const data = await res.json().catch(() => ({}))

      if (res.status === 404) {
        setError('No session found for this ID. Please double-check your Prolific ID.')
        setLoading(false)
        return
      }
      if (!res.ok) {
        setError(data.error || 'Something went wrong. Please try again.')
        setLoading(false)
        return
      }

      setCondition(data.condition)
    } catch {
      setError('Connection failed. Please check your internet connection.')
      setLoading(false)
    }
  }

  // ponytail: study_info was shown in ConsentPage; skip it inside the iframe
  if (condition) {
    return <App condition={condition} tasks={tasksPerCondition[condition]} directStartPid={pid.trim()} />
  }

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-stone-900 mb-2">Welcome Back</h1>
          <p className="text-stone-500 text-sm leading-relaxed">
            Enter your Prolific ID to sync your session and continue the study.
          </p>
        </div>
        <Card className="border border-stone-200 shadow-sm">
          <CardBody className="p-6">
            <form onSubmit={handleSync} className="space-y-4">
              <Input
                label="Your Prolific ID"
                labelPlacement="outside"
                placeholder="e.g. 5f8a1b2c3d4e5f6a7b8c9d0e"
                value={pid}
                onValueChange={setPid}
                isDisabled={loading}
                isInvalid={!!error}
                errorMessage={error}
                autoComplete="off"
              />
              <Button
                type="submit"
                color="primary"
                className="w-full font-semibold"
                isDisabled={!pid.trim() || loading}
                isLoading={loading}
              >
                {loading ? 'Syncing session…' : 'Continue Study'}
              </Button>
            </form>
          </CardBody>
        </Card>
        <p className="text-center text-stone-400 text-xs mt-6">Aalto University · Department of Computer Science</p>
      </div>
    </div>
  )
}
