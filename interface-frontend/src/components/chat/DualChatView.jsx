import { forwardRef, useContext, useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Button, Chip } from '@nextui-org/react'
import { ArrowUpIcon, BrainIcon, ChevronDownIcon, SquareIcon, SquarePen } from 'lucide-react'
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

const Reasoning = ({ text }) => (
  <details className='mb-4 w-full rounded-lg border px-3 py-2 group'>
    <summary className='cursor-pointer flex items-center gap-2 py-1 text-sm text-[#888] hover:text-[#0d0d0d] transition-colors list-none [&::-webkit-details-marker]:hidden'>
      <BrainIcon className='size-4 shrink-0' />
      <span>Reasoning</span>
      <ChevronDownIcon className='size-4 shrink-0 transition-transform group-open:rotate-0 -rotate-90' />
    </summary>
    <div className='relative overflow-hidden max-h-64 overflow-y-auto pt-2 pb-2 ps-6 text-sm text-[#888] leading-relaxed whitespace-pre-wrap'>{text}</div>
  </details>
)

const Column = forwardRef(({ messages, streamContent, streamReasoning, streaming }, ref) => (
  <div ref={ref} className='flex-1 overflow-y-auto px-4 py-4 min-w-0'>
    <div className='flex flex-col gap-4 max-w-lg mx-auto'>
      {messages.map((msg, i) => (
        msg.role === 'user' ? (
          <div key={i} className='self-end max-w-[85%]'>
            <div className='rounded-3xl bg-[#f4f4f4] px-5 py-2.5 text-[#0d0d0d] whitespace-pre-wrap'>{msg.content}</div>
          </div>
        ) : (
          <div key={i} className='max-w-full'>
            {msg.reasoning && <Reasoning text={msg.reasoning} />}
            <Md>{msg.content}</Md>
            {msg.error && <p className='mt-2 text-sm text-red-600'>{msg.error}</p>}
          </div>
        )
      ))}
      {streaming && streamReasoning && !streamContent && <Reasoning text={streamReasoning} />}
      {streaming && streamContent && <div className='max-w-full'><Md>{streamContent}</Md></div>}
      {streaming && !streamContent && !streamReasoning && <div className='py-2'><span className='animate-pulse text-xl text-[#0d0d0d]'>●</span></div>}
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
  const [reasoningA, setReasoningA] = useState('')
  const [reasoningB, setReasoningB] = useState('')
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

    // ponytail: buffer both streams, flush to React on a shared rAF so columns appear in sync
    const buf = { a: '', b: '', ra: '', rb: '', doneA: false, doneB: false }
    let rafId = requestAnimationFrame(function tick () {
      const bothStarted = (buf.a || buf.ra || buf.doneA) && (buf.b || buf.rb || buf.doneB)
      if (bothStarted) { setStreamA(buf.a); setStreamB(buf.b); setReasoningA(buf.ra); setReasoningB(buf.rb) }
      if (!buf.doneA || !buf.doneB) rafId = requestAnimationFrame(tick)
    })

    const streamCol = async (backendMsgs, bufKey, setMsgs, column) => {
      let content = ''
      let reasoning = ''
      let response = null
      let error = null
      const rKey = `r${bufKey}`

      try {
        for await (const event of requestChatResponseStream(backendMsgs, controller.signal, hasTaskQuestion, column)) {
          if (event.type === 'reasoning') {
            reasoning = event.reasoning || (reasoning + (event.delta || ''))
            buf[rKey] = reasoning
          }
          if (event.type === 'delta') {
            content = event.content || (content + (event.delta || ''))
            buf[bufKey] = content
          }
          if (event.type === 'done') response = event.response
        }
      } catch (e) {
        if (controller.signal.aborted) return null
        error = String(e?.message || e)
      }

      buf[bufKey] = ''
      buf[rKey] = ''
      buf[bufKey === 'a' ? 'doneA' : 'doneB'] = true

      if (!response) {
        response = { choices: [{ index: 0, message: { role: 'assistant', content }, finish_reason: error ? 'error' : 'stop' }] }
      }

      setMsgs(prev => [...prev, { role: 'assistant', content, ...(reasoning ? { reasoning } : {}), ...(error ? { error } : {}) }])
      return { role: 'assistant', column, ...response, ...(error ? { error } : {}), render_complete: Date.now(), survey_index: sourceIndex }
    }

    const [resA, resB] = await Promise.all([
      streamCol(backendA, 'a', setMessagesA, 'a'),
      streamCol(backendB, 'b', setMessagesB, 'b')
    ])
    cancelAnimationFrame(rafId)
    setStreamA('')
    setStreamB('')
    setReasoningA('')
    setReasoningB('')

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

  // Clean chat: clears both columns. Past exchanges are already in the store, so the
  // saved data keeps everything. Disabled while streaming so an aborted column can't
  // append its partial reply into the freshly cleared view.
  const handleNewChat = () => {
    setMessagesA([])
    setMessagesB([])
    engagedRef.current.delete(sourceIndexRef.current)
    ctxStore.dispatch({
      type: 'LOG_INTERACTION',
      payload: { type: 'chat_reset', taskId: sourceIndexRef.current, timestamp: Date.now() }
    })
  }

  if (!ctxStore.state.chatEnabled) {
    return <div className='flex flex-1 flex-col h-screen border-l border-[#e5e5e5] bg-[#fafafa]' />
  }

  return (
    <div className='flex flex-1 flex-col h-screen border-l border-[#e5e5e5] bg-[#fafafa]'>
      <div className='flex justify-between items-center w-full px-4 py-3 border-b border-[#e5e5e5]'>
        <Chip color='success' variant='dot'>AI Assistant</Chip>
        <Button size='sm' variant='light' isDisabled={streaming}
          onClick={handleNewChat} startContent={<SquarePen className='size-4' />}>
          New chat
        </Button>
      </div>

      <div className='flex flex-1 min-h-0'>
        <div className='flex flex-col flex-1 min-w-0'>
          <div className='text-center text-xs text-[#888] py-1 border-b border-[#e5e5e5] bg-[#fafafa]'>Response A</div>
          <Column ref={colARef} messages={messagesA} streamContent={streamA} streamReasoning={reasoningA} streaming={streaming} />
        </div>
        <div className='w-px bg-[#e5e5e5]' />
        <div className='flex flex-col flex-1 min-w-0'>
          <div className='text-center text-xs text-[#888] py-1 border-b border-[#e5e5e5] bg-[#fafafa]'>Response B</div>
          <Column ref={colBRef} messages={messagesB} streamContent={streamB} streamReasoning={reasoningB} streaming={streaming} />
        </div>
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
