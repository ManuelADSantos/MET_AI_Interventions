import { useContext, useEffect, useState } from 'react'
import { store } from '../../scripts/store'
import { saveToDatabase } from '../../scripts/dbService'
import { copyToClipboard } from '../../lib/utils'
import { Button, Spinner } from '@nextui-org/react'

const DonePage = () => {
  const {dispatch, state} = useContext(store)
  const [isSaving, setIsSaving] = useState(true)
  const [saveSuccess, setSaveSuccess] = useState(undefined)
  const [errorMessage, setErrorMessage] = useState('')
  const [prolificCode, setProlificCode] = useState('')
  const [prolificUrl, setProlificUrl] = useState('')
  const [copied, setCopied] = useState(false)
  const [attempt, setAttempt] = useState(1)

  useEffect(() => {
    dispatch({ type: 'ALL_DONE' })
    tryToSave()
  }, [])

  const buildPayload = () => {
    const params = new URLSearchParams(window.location.search)
    return {
      participantId: state.participantId,
      condition: state.condition,
      messages: state.messages,
      interactionLog: state.interactionLog,
      tasks: state.tasks,
      studyId: params.get('STUDY_ID') || '',
      sessionId: params.get('SESSION_ID') || ''
    }
  }

  const tryToSave = async () => {
    setSaveSuccess(undefined)
    setIsSaving(true)
    const payload = buildPayload()

    // ponytail: 3 auto-attempts before bothering the participant — the observed failure
    // (proxy silently dropping a response) is transient, a retry seconds later succeeds
    let res
    for (let i = 1; i <= 3; i++) {
      setAttempt(i)
      res = await saveToDatabase(payload)
      if (!res.error) break
      if (i < 3) await new Promise(r => setTimeout(r, 3000))
    }

    if (res.error) {
      setErrorMessage(res.error)
      setSaveSuccess(false)
      setIsSaving(false)
      return
    }

    setSaveSuccess(true)
    setIsSaving(false)
    setProlificCode(res.prolificCode)
    setProlificUrl(res.prolificUrl)
  }

  // Last-resort escape hatch: the responses as a downloadable file, so a dead backend
  // can never cost the participant their hour of work
  const downloadData = () => {
    const blob = new Blob([JSON.stringify(buildPayload(), null, 2)], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `study_responses_${state.participantId}.json`
    a.click()
    URL.revokeObjectURL(a.href)
  }

  return (
    <div className='justify-self-center self-center text-center mb-2'>
      <h1 className='text-3xl font-bold mb-4'>All done! 🎉</h1>
      {/* Show loading spinner when saving */}
      {isSaving && <div>
        <Spinner className='my-4' />
        <p className='italic'>Saving your responses...{attempt > 1 ? ` (attempt ${attempt} of 3)` : ''}</p>
      </div>}
      {/* Show error message & retry button if save failed */}
      {saveSuccess === false && <div>
        <p className='text-red-500 my-4'>{errorMessage}</p>
        <Button color='danger' onClick={() => tryToSave()}>Try again</Button>
        <p className='mt-6 text-sm text-gray-600'>
          If this keeps failing, please{' '}
          <button className='text-blue-500 underline' onClick={downloadData}>download your responses</button>
          {' '}and send the file to the researcher via a Prolific message.
        </p>
      </div>}
      {/* Show completion instructions once save succeeds */}
      {saveSuccess === true && <div>
        <p>Thank you for taking part in the study!</p>
        <p className='my-4 font-bold'>Please copy this completion code:</p>
        <div className='flex items-center justify-center gap-2 my-2'>
          <p className='font-mono p-4 bg-stone-200 select-all cursor-pointer'>{prolificCode}</p>
          <Button size='sm' variant='flat' onClick={async () => {
            setCopied(await copyToClipboard(prolificCode) ? 'ok' : 'fail')
            setTimeout(() => setCopied(false), 2000)
          }}>
            {copied === 'ok' ? 'Copied!' : copied === 'fail' ? 'Copy failed' : 'Copy'}
          </Button>
        </div>
        {import.meta.env.VITE_USE_AUTOPROCTOR === 'true'
          ? <p className='text-xl font-semibold mt-8'>
              Then press <strong>'Click After Submitting Test'</strong> to complete your session.
            </p>
          : <>
              <p className='my-4 font-bold'>To register your participation on Prolific, navigate to the following URL:</p>
              <p className='text-blue-500 hover:underline my-8'><a href={prolificUrl}>{prolificUrl}</a></p>
            </>
        }
      </div>}
    </div>
  )
}

export default DonePage
