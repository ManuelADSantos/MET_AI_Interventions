import { useContext, useState } from 'react'
import { Button, Spinner, Textarea } from '@nextui-org/react'
import { store } from '../../scripts/store'
import { requestChatResponseStream } from '../../scripts/chatService'
import { buildTranscript, contributionStats, coverage, parseSummary, scopeMessages } from '../../scripts/reflectionSummary'

const MIN_CHARS = 200

const reviewerPrompt = (transcript, explainBack) =>
  `You are reviewing a transcript of someone solving planning puzzles with the help of an AI assistant. You are NOT the assistant they talked to and you have no stake in it. Be factual and neutral: no praise, no criticism, no score, no advice.

TRANSCRIPT:
<<<${transcript}>>>

WHAT THEY WROTE AFTERWARDS FROM MEMORY, WITHOUT ACCESS TO THE TRANSCRIPT:
<<<${explainBack}>>>

Return ONLY minified JSON, no prose and no code fences:
{"problems":[{"item":"<one key problem the tasks actually required solving, max 20 words, phrased as something they solved>","covered":true|false}],"learning":[{"item":"<one concept or skill someone would need to understand to do this without AI, max 20 words>","covered":true|false}]}
Give 3 to 5 problems and 3 to 5 learning items. Set "covered" to true only when their from-memory text clearly shows that item; when in doubt set it to false.`

const Item = ({ text, covered }) => (
  <li className='flex items-start gap-2 mb-2'>
    <span className={covered ? 'text-emerald-600' : 'text-stone-400'}>{covered ? '✓' : '○'}</span>
    <span className={covered ? '' : 'text-stone-700'}>{text}</span>
  </li>
)

/** scopeIds: sourceIndexes this reflection covers, or null for the whole study.
 *  storeKey: where the answers land in state.tasks.
 *  final: only the end-of-study reflection asks the 0-12 estimate. */
const ReflectionPage = ({ storeKey, scopeIds = null, final = false, label = '', next }) => {
  const { dispatch, state } = useContext(store)
  const [explainBack, setExplainBack] = useState('')
  const [withoutAi, setWithoutAi] = useState('')
  const [stage, setStage] = useState('a')
  const [summary, setSummary] = useState(null)
  const [rawFallback, setRawFallback] = useState('')
  const [postEstimate, setPostEstimate] = useState('')

  const scoped = scopeMessages(state.messages, scopeIds)
  const stats = contributionStats(scoped)
  const partA = {
    [`${storeKey}.1`]: { question: 'Explain back: what was the solution and why does it work?', answer: explainBack },
    [`${storeKey}.2`]: { question: 'Could you do this again without AI? (0-100%)', answer: withoutAi }
  }

  const submitPartA = async () => {
    setStage('loading')
    dispatch({ type: 'UPDATE_RESPONSES', payload: { index: storeKey, responses: partA } })

    try {
      let out = ''
      for await (const event of requestChatResponseStream([
        { role: 'user', content: reviewerPrompt(buildTranscript(scoped), explainBack) }
      ])) {
        if (event.type === 'delta') out = event.content || out + (event.delta || '')
        if (event.type === 'done') out = out || event.response?.choices?.[0]?.message?.content || ''
      }
      setSummary(parseSummary(out))
    } catch (e) {
      // ponytail: never trap the participant before /save runs — show what we got and move on
      setRawFallback(String(e.message || e))
      dispatch({ type: 'LOG_INTERACTION', payload: { type: 'reflection_summary_failed', timestamp: Date.now(), error: String(e.message || e) } })
    }
    setStage('b')
  }

  const finish = () => {
    dispatch({
      type: 'UPDATE_RESPONSES',
      payload: {
        index: storeKey,
        responses: {
          ...partA,
          ...(final ? { [`${storeKey}.3`]: { question: 'After the reflection: how many of the 12 problems could you solve without AI?', answer: postEstimate } } : {}),
          [`${storeKey}.4`]: { question: 'Reflection coverage (problems)', answer: summary ? coverage(summary.problems) : 'n/a' },
          [`${storeKey}.5`]: { question: 'Reflection coverage (learning)', answer: summary ? coverage(summary.learning) : 'n/a' }
        }
      }
    })
    next()
  }

  if (stage === 'a') {
    return (
      <div className='flex flex-1 flex-col w-full overflow-auto'>
        <h1 className='text-4xl font-bold mb-4'>{final ? 'Before we finish' : 'Pause and reflect'}</h1>
        <p className='mb-4'>
          {final
            ? 'The AI is no longer available, and you cannot go back to the conversation.'
            : `Before moving on${label ? ` from ${label}` : ''}: answer from memory. Do not scroll back through the conversation.`}
        </p>

        <p className='font-semibold mb-2'>{final ? 'Could you do these tasks again without AI?' : 'Could you do this again without AI?'}</p>
        <input
          type='number' min={0} max={100} value={withoutAi}
          onChange={(e) => setWithoutAi(e.target.value)}
          className='mb-6 w-32 border border-stone-300 rounded px-2 py-1'
          placeholder='0-100'
        />

        <p className='font-semibold mb-2'>
          In your own words, explain what the solution was and why it works. What were the key problems that had to be solved here?
        </p>
        <Textarea
          minRows={8} value={explainBack}
          onChange={(e) => setExplainBack(e.target.value)}
          placeholder='Write from memory.'
          variant='bordered'
        />
        <p className='text-sm text-stone-500 mt-1 mb-4'>
          <span className={explainBack.trim().length >= MIN_CHARS ? 'text-emerald-600 font-semibold' : 'text-red-600 font-semibold'}>{explainBack.length}</span> / {MIN_CHARS} characters minimum
        </p>

        <Button
          color='primary' className='self-end'
          isDisabled={explainBack.trim().length < MIN_CHARS || withoutAi === ''}
          onClick={submitPartA}
        >
          Submit
        </Button>
      </div>
    )
  }

  if (stage === 'loading') {
    return (
      <div className='self-center justify-self-center text-center'>
        <Spinner className='my-4' />
        <p className='italic'>Reviewing your work...</p>
      </div>
    )
  }

  return (
    <div className='flex flex-1 flex-col w-full overflow-auto'>
      <h1 className='text-4xl font-bold mb-4'>What you took away</h1>

      {summary
        ? <>
            <h2 className='text-xl font-semibold mt-2 mb-2'>The key problems you solved</h2>
            <ul>{summary.problems.map((p, i) => <Item key={i} text={p.item} covered={p.covered} />)}</ul>

            <h2 className='text-xl font-semibold mt-6 mb-2'>What you'd need to understand to do this without AI</h2>
            <ul>{summary.learning.map((p, i) => <Item key={i} text={p.item} covered={p.covered} />)}</ul>
            <p className='text-sm text-stone-500 mt-2'>✓ = your explanation covered this · ○ = it did not come up</p>
          </>
        : <p className='text-stone-600 mb-4'>We could not generate the review this time{rawFallback ? '.' : '.'} Your answers were still recorded.</p>
      }

      <h2 className='text-xl font-semibold mt-6 mb-2'>Where the work came from</h2>
      <p>You wrote {stats.words} words. The AI replied {stats.aiReplies} times. You re-prompted {stats.reprompts} times.</p>

      {final && <>
        <p className='font-semibold mt-8 mb-2'>Now that you have seen this: how many of the 12 problems could you solve on your own, without AI?</p>
        <input
          type='number' min={0} max={12} value={postEstimate}
          onChange={(e) => setPostEstimate(e.target.value)}
          className='mb-6 w-32 border border-stone-300 rounded px-2 py-1'
          placeholder='0-12'
        />
      </>}

      <Button color='primary' className='self-end mt-8' isDisabled={final && postEstimate === ''} onClick={finish}>
        {final ? 'Finish' : 'Continue'}
      </Button>
    </div>
  )
}

export default ReflectionPage
