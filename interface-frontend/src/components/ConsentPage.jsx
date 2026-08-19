import { useState, useMemo } from 'react'
import { Button, Card, CardBody, Checkbox } from '@nextui-org/react'
import { Monitor, IdCard } from 'lucide-react'
import { copyToClipboard } from '../lib/utils'
import loadTasks from '../scripts/taskParser/taskParser'

// ponytail: auto-discover study info files by condition name
const studyInfoFiles = import.meta.glob('/customizations/study_info/*_studyinfo.md', { query: '?raw', import: 'default', eager: true })

const baseURL = import.meta.env.VITE_PROXY_URL || ''

function renderBold(text) {
  return text.split(/(\*\*[^*]+\*\*)/).map((part, i) =>
    part.startsWith('**')
      ? <strong key={i} className="text-stone-900">{part.slice(2, -2)}</strong>
      : part
  )
}

function ContentBlock({ block }) {
  if (block.type === 'h2') return <h2 className="text-stone-900 font-semibold text-sm uppercase tracking-wide mt-5 mb-1 first:mt-0">{block.text}</h2>
  if (block.type === 'h3') return <h3 className="text-stone-800 font-medium text-sm mt-3 mb-1">{block.text}</h3>
  if (block.type === 'paragraph') {
    const lines = block.text.split('\n').filter(l => l.trim())
    const isList = lines.length > 1 && lines.every(l => l.trim().startsWith('-'))
    if (isList) {
      return (
        <ul className="list-disc list-inside space-y-1 pl-1">
          {lines.map((l, i) => <li key={i} className="text-stone-700 text-sm">{renderBold(l.replace(/^[\s-]+/, ''))}</li>)}
        </ul>
      )
    }
    return <p className="text-stone-700 text-sm leading-relaxed">{renderBold(block.text)}</p>
  }
  return null
}

function CopyPidButton({ pid }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = async () => {
    if (!await copyToClipboard(pid)) return // the ID is shown next to the button; copy by hand
    setCopied(true)
    setTimeout(() => setCopied(false), 2500)
  }
  return (
    <div className="bg-white border border-stone-300 rounded-lg p-4">
      <p className="text-stone-700 text-xs mb-2 uppercase tracking-wide font-bold">Your Prolific ID</p>
      <div className="flex items-center gap-3">
        <code className="text-blue-600 text-sm font-mono flex-1 break-all">{pid}</code>
        <Button size="sm" variant="flat" color={copied ? 'success' : 'default'} onPress={handleCopy}>
          {copied ? '✓ Copied' : 'Copy'}
        </Button>
      </div>
      <p className="text-stone-500 text-xs mt-2">Save this — you'll need it to log in after AutoProctor opens the study.</p>
    </div>
  )
}

export default function ConsentPage({ prolificPid, prolificStudyId, prolificSessionId, condition }) {
  const [step, setStep] = useState(0)
  const [briefingConsentGiven, setBriefingConsentGiven] = useState(false)
  const [finalConsentGiven, setFinalConsentGiven] = useState(false)
  const [pidCopied, setPidCopied] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const allSteps = useMemo(() => {
    const key = `/customizations/study_info/${condition.replace(/-/g, '_')}_studyinfo.md`
    const raw = studyInfoFiles[key] || ''
    const parsed = loadTasks(raw)

    const briefingSteps = parsed.map(page => ({
      kind: 'briefing',
      title: page.title,
      content: page.content,
      hasIAgree: page.content.some(b => b.type === 'option'),
    }))

    return [
      ...briefingSteps,
      { kind: 'proctor', title: 'Study Monitoring', key: 'monitoring' },
      { kind: 'proctor', title: 'Agreement & Setup', key: 'agreement' },
    ]
  }, [condition])

  const currentStep = allSteps[step]
  const isLastStep = step === allSteps.length - 1
  const isBriefingIAgreeStep = currentStep?.kind === 'briefing' && currentStep.hasIAgree
  const canAdvance = isBriefingIAgreeStep ? briefingConsentGiven : true

  const handleAgreeAndStart = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${baseURL}/api/launch/consent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prolificPid, condition, prolificStudyId, prolificSessionId }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || 'Something went wrong.')
        setLoading(false)
        return
      }
      window.location.href = data.autoproctor_url
    } catch {
      setError('Connection failed. Please check your internet connection.')
      setLoading(false)
    }
  }

  if (!currentStep) return null

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="flex gap-1 mb-6">
          {allSteps.map((_, i) => (
            <div key={i} className={`h-1 flex-1 rounded-full transition-colors duration-300 ${i <= step ? 'bg-blue-500' : 'bg-stone-200'}`} />
          ))}
        </div>

        <Card className="border border-stone-200 shadow-sm">
          <CardBody className="p-6 md:p-8">
            <p className="text-xs text-stone-500 uppercase tracking-widest mb-1">Step {step + 1} of {allSteps.length}</p>
            <h1 className="text-xl font-bold text-stone-900 mb-5">{currentStep.title}</h1>

            {currentStep.kind === 'briefing' && (
              <>
                <div className="space-y-3">
                  {currentStep.content.map((block, i) => <ContentBlock key={i} block={block} />)}
                </div>
                {isBriefingIAgreeStep && (
                  <div className="mt-6 pt-4 border-t border-stone-200">
                    <Button
                      color={briefingConsentGiven ? 'success' : 'primary'}
                      variant={briefingConsentGiven ? 'flat' : 'solid'}
                      onPress={() => setBriefingConsentGiven(true)}
                    >
                      {briefingConsentGiven ? '✓ I agree' : 'I agree'}
                    </Button>
                  </div>
                )}
              </>
            )}

            {currentStep.key === 'monitoring' && (
              <div className="space-y-3 text-stone-700 text-sm leading-relaxed">
                <p>
                  This study uses <strong className="text-stone-900">AutoProctor</strong> — a browser-based
                  proctoring tool — to ensure study integrity.
                </p>
                <p>AutoProctor will:</p>
                <ul className="list-disc list-inside space-y-1 pl-1">
                  <li>Monitor your <strong className="text-stone-900">screen</strong> to track which page you are focusing on</li>
                  <li>Detect <strong className="text-stone-900">tab switches</strong> or navigation away from the study</li>
                  <li>Check for <strong className="text-stone-900">external monitors</strong> — you must use only one screen in full-screen mode</li>
                </ul>
                <p>Proctoring data is processed under AutoProctor's privacy policy and deleted after the study review period.</p>
                <div className="mt-2 rounded-lg border-2 border-amber-400 bg-amber-50 p-4 space-y-2">
                  <p className="font-bold text-amber-900 flex items-center gap-2">
                    <Monitor className='size-5' /> Screen access is required
                  </p>
                  <p className="text-amber-800">
                    When prompted by your browser, you <strong>must grant screen access</strong> for the study to proceed.
                  </p>
                  <p className="text-amber-800">
                    If you do not consent to proctoring, please <strong>return this study on Prolific</strong> now.
                  </p>
                </div>
              </div>
            )}

            {currentStep.key === 'agreement' && (
              <div className="space-y-3 text-stone-700 text-sm leading-relaxed">
                <p>Participation is entirely voluntary. You have the right to:</p>
                <ul className="list-disc list-inside space-y-1 pl-1">
                  <li>Withdraw at any time without penalty (return the study on Prolific)</li>
                  <li>Request deletion of your data by contacting the researcher</li>
                </ul>
                <p>
                  For questions, contact the principal investigator:{' '}
                  <strong className="text-stone-900">Robin Welsch</strong> — robin.welsch@aalto.fi
                </p>
                <div className="mt-6 pt-5 border-t border-stone-200 space-y-4">
                  <div className="rounded-lg border-2 border-yellow-400 bg-yellow-50 p-4 space-y-3">
                    <p className="font-bold text-stone-900 flex items-center gap-2">
                      <IdCard className='size-5' /> Do not use your real name in AutoProctor
                    </p>
                    <p className="text-stone-800 text-sm leading-relaxed">
                      When AutoProctor opens, it will ask for your name.{' '}
                      <strong>You must paste your Prolific ID there — not your real name.</strong>
                    </p>
                    <p className="text-stone-800 text-sm">Copy your Prolific ID now using the button below:</p>
                    <CopyPidButton pid={prolificPid} />
                    <Checkbox
                      isSelected={pidCopied}
                      onValueChange={setPidCopied}
                      isDisabled={loading}
                      classNames={{ label: 'text-stone-900 text-sm font-medium' }}
                    >
                      I have copied my Prolific ID and will paste it when AutoProctor asks for my name
                    </Checkbox>
                  </div>
                  <Checkbox
                    isSelected={finalConsentGiven}
                    onValueChange={setFinalConsentGiven}
                    isDisabled={loading}
                    classNames={{ label: 'text-stone-700 text-sm' }}
                  >
                    I have read and understood the above. I agree to participate and to be monitored via AutoProctor.
                  </Checkbox>
                  {error && <p className="text-red-600 text-sm">{error}</p>}
                </div>
              </div>
            )}

            <div className="flex justify-between mt-8">
              <Button
                variant="flat"
                onPress={() => { setStep(s => s - 1); setBriefingConsentGiven(false) }}
                isDisabled={step === 0 || loading}
              >
                Back
              </Button>

              {isLastStep ? (
                <Button
                  color="primary"
                  onPress={handleAgreeAndStart}
                  isDisabled={!finalConsentGiven || !pidCopied || loading}
                  isLoading={loading}
                >
                  {loading ? 'Setting up your session…' : 'Agree & Start Study'}
                </Button>
              ) : (
                <Button color="primary" onPress={() => setStep(s => s + 1)} isDisabled={!canAdvance}>
                  Next
                </Button>
              )}
            </div>
          </CardBody>
        </Card>

        <p className="text-center text-stone-400 text-xs mt-4">Aalto University · Department of Computer Science</p>
      </div>
    </div>
  )
}
