import { useContext, useEffect, useState } from 'react'
import { Button, Spinner } from '@nextui-org/react'
import { store } from '../../scripts/store'
import { requestChatResponseStream } from '../../scripts/chatService'
import { buildTranscript, contributionStats, coverage, parseSummary, scopeMessages } from '../../scripts/reflectionSummary'

/* The AI's review of what the participant took away, shown after a `:::reflect-summary` page's
 * questions are submitted. Everything else about a reflection lives in the markdown file; this is
 * the one part that cannot, because it needs a model call over the transcript. */

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

/** scopeIds: sourceIndexes whose chat this review covers. explainBack: what they wrote from memory. */
const ReflectionSummary = ({ sourceIndex, scopeIds, explainBack, onContinue, isLast }) => {
  const { dispatch, state } = useContext(store)
  const [loading, setLoading] = useState(true)
  const [summary, setSummary] = useState(null)

  const scoped = scopeMessages(state.messages, scopeIds)
  const stats = contributionStats(scoped)

  useEffect(() => { review() }, [])

  const review = async () => {
    try {
      let out = ''
      for await (const event of requestChatResponseStream([
        { role: 'user', content: reviewerPrompt(buildTranscript(scoped), explainBack) }
      ])) {
        if (event.type === 'delta') out = event.content || out + (event.delta || '')
        if (event.type === 'done') out = out || event.response?.choices?.[0]?.message?.content || ''
      }
      const parsed = parseSummary(out)
      setSummary(parsed)
      // ponytail: coverage is a derived manipulation-check measure, so it goes in the interaction log
      // rather than into the page's responses — UPDATE_RESPONSES replaces them wholesale.
      dispatch({ type: 'LOG_INTERACTION', payload: {
        type: 'reflection_coverage',
        taskId: sourceIndex,
        timestamp: Date.now(),
        scopeIds,
        problems: parsed ? coverage(parsed.problems) : 'n/a',
        learning: parsed ? coverage(parsed.learning) : 'n/a',
        ...stats
      }})
    } catch (e) {
      // ponytail: never trap the participant before /save runs — show what we have and move on
      dispatch({ type: 'LOG_INTERACTION', payload: {
        type: 'reflection_summary_failed', taskId: sourceIndex, timestamp: Date.now(), error: String(e.message || e)
      }})
    }
    setLoading(false)
  }

  if (loading) {
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
        : <p className='text-stone-600 mb-4'>We could not generate the review this time. Your answers were still recorded.</p>
      }

      <h2 className='text-xl font-semibold mt-6 mb-2'>Where the work came from</h2>
      <p>You wrote {stats.words} words. The AI replied {stats.aiReplies} times. You re-prompted {stats.reprompts} times.</p>

      <Button color='primary' className='self-end mt-8' onClick={onContinue}>{isLast ? 'Finish' : 'Continue'}</Button>
    </div>
  )
}

export default ReflectionSummary
