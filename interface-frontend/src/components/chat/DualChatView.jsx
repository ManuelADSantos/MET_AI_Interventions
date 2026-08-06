import { forwardRef, useContext, useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Chip } from '@nextui-org/react'
import { ArrowUpIcon, SquareIcon } from 'lucide-react'
import { store } from '../../scripts/store'
import { requestChatResponseStream } from '../../scripts/chatService'
import { interventionGate, questionTerms, QUESTION_THRESHOLD } from '../../scripts/taskQuestion'

// ponytail: markdown styles via Tailwind descendant selectors — no @tailwindcss/typography dep
const md = [
  '[&_h2]:text-lg [&_h2]:font-semibold [&_h2]:my-3 [&_h2]:first:mt-0',
  '[&_h3]:text-base [&_h3]:font-semibold [&_h3]:my-2',
  '[&_p]:my-2 [&_p:first-child]:mt-0 [&_p:last-child]:mb-0',
  '[&_ul]:my-2 [&_ul]:ml-5 [&_ul]:list-disc [&_ol]:my-2 [&_ol]:ml-5 [&_ol]:list-decimal',
  '[&_li]:mt-1 [&_li]:leading-relaxed',
  '[&_strong]:font-semibold',
  '[&_code]:bg-[#f4f4f4] [&_code]:rounded [&_code]:px-1 [&_code]:py-0.5 [&_code]:text-[0.9em]',
  '[&_table]:w-full [&_table]:border-collapse [&_table]:my-3',
  '[&_th]:border [&_th]:border-[#d4d4d4] [&_th]:px-3 [&_th]:py-1.5 [&_th]:bg-[#f3f4f6] [&_th]:text-left [&_th]:text-sm [&_th]:font-semibold',
  '[&_td]:border [&_td]:border-[#e5e7eb] [&_td]:px-3 [&_td]:py-1.5 [&_td]:text-sm',
].join(' ')

const Md = ({ children }) => (
  <div className={`text-[#0d0d0d] leading-relaxed ${md}`}>
    <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
  </div>
)

const Column = forwardRef(({ messages, streamContent, streaming }, ref) => (
  <div ref={ref} className='flex-1 overflow-y-auto px-4 py-4 min-w-0'>
    <div className='flex flex-col gap-4 max-w-lg mx-auto'>
      {messages.map((msg, i) => (
        msg.role === 'user' ? (
          <div key={i} className='self-end max-w-[85%]'>
            <div className='rounded-3xl bg-[#f4f4f4] px-5 py-2.5 text-[#0d0d0d] whitespace-pre-wrap'>{msg.content}</div>
          </div>
        ) : (
          <div key={i} className='max-w-full'>
            <Md>{msg.content}</Md>
            {/* A failed or aborted stream has to be visible — otherwise the column just looks
                empty and the participant cannot tell the page is still locked. */}
            {msg.error && <p className='mt-2 text-sm text-red-600'>{msg.error}</p>}
          </div>
        )
      ))}
      {streaming && streamContent && <div className='max-w-full'><Md>{streamContent}</Md></div>}
      {streaming && !streamContent && <div className='py-2'><span className='animate-pulse text-xl text-[#0d0d0d]'>●</span></div>}
    </div>
  </div>
))

const DualChatView = ({ task }) => {
  const sourceIndex = task?.sourceIndex
  const ctxStore = useContext(store)
  const engagedRef = useRef(new Set())
  // Tracks the page the participant is on *now*, so a stream that finishes after they navigate
  // cannot unlock a page they never prompted on (`sourceIndex` alone is captured in the closure).
  const sourceIndexRef = useRef(sourceIndex)
  sourceIndexRef.current = sourceIndex
  const colARef = useRef(null)
  const colBRef = useRef(null)
  const abortRef = useRef(null)
  const inputRef = useRef(null)

  const [messagesA, setMessagesA] = useState([])
  const [messagesB, setMessagesB] = useState([])
  const [streamA, setStreamA] = useState('')
  const [streamB, setStreamB] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [input, setInput] = useState('')

  // Auto-scroll both columns
  useEffect(() => { colARef.current && (colARef.current.scrollTop = colARef.current.scrollHeight) }, [messagesA, streamA])
  useEffect(() => { colBRef.current && (colBRef.current.scrollTop = colBRef.current.scrollHeight) }, [messagesB, streamB])

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 128)}px`
    }
  }, [input])

  // Abort on unmount
  useEffect(() => () => { abortRef.current?.abort() }, [])

  // Task draft bridge (copy button in TaskView)
  useEffect(() => {
    const handler = (event) => {
      const { text, focusOnly, onInserted } = event.detail || {}
      if (!focusOnly && text) {
        setInput(prev => {
          const next = prev.trim() ? `${prev.trim()}\n\n${text}` : text
          onInserted?.(next)
          return next
        })
      }
      requestAnimationFrame(() => inputRef.current?.focus())
    }
    window.addEventListener('study:add-task-to-chat', handler)
    return () => window.removeEventListener('study:add-task-to-chat', handler)
  }, [])

  const submit = async () => {
    if (!input.trim() || streaming) return
    const text = input.trim()
    setInput('')

    if (ctxStore.state.displayChatOnboarding) {
      ctxStore.dispatch({ type: 'DISMISS_ONBOARDING' })
    }

    const { hasTaskQuestion, coverage } = interventionGate(
      engagedRef.current, sourceIndex, text, questionTerms(task)
    )
    if (coverage !== null) {
      ctxStore.dispatch({
        type: 'LOG_INTERACTION',
        payload: { type: 'intervention_gate_test', taskId: sourceIndex, timestamp: Date.now(), coverage, threshold: QUESTION_THRESHOLD, matched: hasTaskQuestion }
      })
    }

    const prompt = { role: 'user', content: text, ts: Date.now(), task: sourceIndex, hasTaskQuestion }

    // Draft tracking (copy button → send)
    const addedDraft = ctxStore.state.taskChatDraft
    if (addedDraft?.taskId === sourceIndex) {
      ctxStore.dispatch({
        type: 'TASK_CHAT_DRAFT_SENT',
        payload: { taskId: sourceIndex, timestamp: prompt.ts, editedBeforeSend: addedDraft.editedBeforeSend || text !== addedDraft.insertedText }
      })
    }

    const userMsg = { role: 'user', content: text }
    setMessagesA(prev => [...prev, userMsg])
    setMessagesB(prev => [...prev, userMsg])
    setStreaming(true)
    setStreamA('')
    setStreamB('')

    const controller = new AbortController()
    abortRef.current = controller

    // Snapshot current messages for the backend (before React applies the state update)
    const backendA = [...messagesA, userMsg].map(m => ({ role: m.role, content: m.content }))
    const backendB = [...messagesB, userMsg].map(m => ({ role: m.role, content: m.content }))

    const streamCol = async (backendMsgs, setStream, setMsgs, column) => {
      let content = ''
      let response = null
      let error = null

      try {
        for await (const event of requestChatResponseStream(backendMsgs, controller.signal, hasTaskQuestion, column)) {
          if (event.type === 'delta') {
            content = event.content || (content + (event.delta || ''))
            setStream(content)
          }
          if (event.type === 'done') response = event.response
        }
      } catch (e) {
        error = String(e?.message || e)
      }

      if (!response) {
        response = { choices: [{ index: 0, message: { role: 'assistant', content }, finish_reason: error ? 'error' : 'stop' }] }
      }

      setMsgs(prev => [...prev, { role: 'assistant', content, ...(error ? { error } : {}) }])
      setStream('')
      return { role: 'assistant', column, ...response, ...(error ? { error } : {}), render_complete: Date.now(), survey_index: sourceIndex }
    }

    const [resA, resB] = await Promise.all([
      streamCol(backendA, setStreamA, setMessagesA, 'a'),
      streamCol(backendB, setStreamB, setMessagesB, 'b')
    ])

    setStreaming(false)

    ctxStore.dispatch({
      type: 'UPDATE_MESSAGES',
      payload: { prompt: { ...prompt, hasTaskQuestion }, response: resA, response_b: resB }
    })

    // Unlock progression only if the participant is still on the page where generation started.
    if (!resA.error && !resB.error && sourceIndexRef.current === sourceIndex) {
      ctxStore.dispatch({ type: 'TOGGLE_CHAT_USED', payload: { value: true } })
    }
  }

  const stop = () => abortRef.current?.abort()

  if (!ctxStore.state.chatEnabled) {
    return <div className='flex flex-1 flex-col h-screen border-l border-[#e5e5e5] bg-[#fafafa]' />
  }

  return (
    <div className='flex flex-1 flex-col h-screen border-l border-[#e5e5e5] bg-[#fafafa]'>
      <div className='flex justify-center items-center w-full py-3 gap-4 border-b border-[#e5e5e5]'>
        <Chip color='primary' variant='dot'>Perspective A</Chip>
        <Chip color='secondary' variant='dot'>Perspective B</Chip>
      </div>

      <div className='flex flex-1 min-h-0'>
        <Column ref={colARef} messages={messagesA} streamContent={streamA} streaming={streaming} />
        <div className='w-px bg-[#e5e5e5]' />
        <Column ref={colBRef} messages={messagesB} streamContent={streamB} streaming={streaming} />
      </div>

      <div className='p-4 border-t border-[#e5e5e5]'>
        <form onSubmit={(e) => { e.preventDefault(); submit() }}>
          <div className='flex items-end gap-2 rounded-[28px] border border-[#e5e5e5] bg-white p-2 shadow-sm max-w-3xl mx-auto'>
            <textarea
              ref={inputRef}
              className='flex-1 resize-none bg-transparent px-3 py-2 text-base outline-none min-h-[40px] max-h-[128px]'
              placeholder='Ask anything'
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() } }}
              rows={1}
              disabled={streaming}
            />
            <button
              type={streaming ? 'button' : 'submit'}
              disabled={!streaming && !input.trim()}
              onClick={streaming ? stop : undefined}
              className='flex h-10 w-10 min-w-10 items-center justify-center rounded-full bg-[#0d0d0d] text-white disabled:bg-[#d7d7d7] transition-colors'
            >
              {streaming ? <SquareIcon className='size-3.5 fill-current' /> : <ArrowUpIcon className='size-4.5' />}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default DualChatView
