import { useContext, useMemo, useRef } from 'react'
import { AssistantRuntimeProvider, SimpleImageAttachmentAdapter, useLocalRuntime } from '@assistant-ui/react'
import { Chip } from '@nextui-org/react'
import { store } from '../../scripts/store'
import { requestChatResponseStream } from '../../scripts/chatService'
import { questionCoverage, questionTerms } from '../../scripts/taskQuestion'
import { Thread } from '../thread'

const enableImages = import.meta.env.VITE_ALLOW_IMAGES ? import.meta.env.VITE_ALLOW_IMAGES === 'true' : true
// ponytail: interventions only engage once the prompt carries the task's actual question. Pasting
// the scenario alone is not enough: `alternatives` would argue four options over statements it has
// never seen and invent them. The score is computed for every condition — cheaper than keeping a
// list of gated conditions in sync with INTERVENTION_PROMPTS in app.py, and it gives the control
// arms the same measure as a covariate.
// intervention_similarity_threshold in study.config.yml; 0.6 when unset.
// `|| NaN` because entrypoint.sh writes an empty value for a missing key, and Number('') is 0 —
// which would silently engage the intervention on every prompt.
const configuredThreshold = Number(import.meta.env.VITE_INTERVENTION_SIMILARITY_THRESHOLD || NaN)
const QUESTION_THRESHOLD = Number.isFinite(configuredThreshold)
  ? Math.min(1, Math.max(0, configuredThreshold))
  : 0.6

const partText = (part) => {
  if (!part) return ''
  return typeof part.text === 'string' ? part.text : ''
}

const messageText = (message) => {
  if (typeof message.content === 'string') return message.content
  if (!Array.isArray(message.content)) return ''
  return message.content.map(partText).filter(Boolean).join('\n')
}

const messageImage = (message) => {
  const contentImage = Array.isArray(message.content)
    ? message.content.find((part) => part?.type === 'image')?.image
    : undefined

  const attachmentImage = message.attachments
    ?.flatMap((attachment) => attachment.content || [])
    ?.find((part) => part?.type === 'image')?.image

  return contentImage || attachmentImage
}

const toBackendMessage = (message) => {
  const image = message.role === 'user' ? messageImage(message) : undefined
  return {
    role: message.role,
    content: messageText(message),
    ...(image ? { image } : {})
  }
}

const ChatView = ({ task }) => {
  const sourceIndex = task?.sourceIndex
  const ctxStore = useContext(store)
  const ctxStoreRef = useRef(ctxStore)
  const sourceIndexRef = useRef(sourceIndex)
  const lastUserMessageIdRef = useRef(undefined)
  const questionTermsRef = useRef(questionTerms(task))
  // ponytail: latched per task — once engaged, the intervention has to survive follow-ups like
  // "use the cheaper option", which score near zero against the question and would drop it
  // mid-conversation (pause-points would abandon its step sequence, alternatives would collapse
  // back to a single answer).
  const engagedTasksRef = useRef(new Set())

  ctxStoreRef.current = ctxStore
  sourceIndexRef.current = sourceIndex
  questionTermsRef.current = questionTerms(task)

  const chatModel = useMemo(() => ({
    async *run({ messages, abortSignal }) {
      const currentStore = ctxStoreRef.current
      const currentSourceIndex = sourceIndexRef.current

      if (currentStore.state.displayChatOnboarding) {
        currentStore.dispatch({ type: 'DISMISS_ONBOARDING' })
      }

      const backendMessages = messages
        .filter((message) => ['user', 'assistant'].includes(message.role))
        .map(toBackendMessage)

      /* Regenerating reruns the SAME user message (same id); a fresh prompt has a new id.
       * Only fresh prompts may unlock page progression below. */
      const newestUiUserMessage = [...messages].reverse().find((message) => message.role === 'user')
      const isNewPrompt = newestUiUserMessage?.id !== lastUserMessageIdRef.current
      lastUserMessageIdRef.current = newestUiUserMessage?.id

      const newestUserMessage = [...backendMessages].reverse().find((message) => message.role === 'user')
      const prompt = {
        role: 'user',
        content: newestUserMessage?.content || '',
        image: newestUserMessage?.image,
        ts: Date.now(),
        task: currentSourceIndex,
        ...(isNewPrompt ? {} : { regenerated: true })
      }

      let hasTaskQuestion = engagedTasksRef.current.has(currentSourceIndex)
      if (!hasTaskQuestion) {
        const coverage = questionCoverage(prompt.content, questionTermsRef.current)
        hasTaskQuestion = coverage >= QUESTION_THRESHOLD
        if (hasTaskQuestion) engagedTasksRef.current.add(currentSourceIndex)
        if (isNewPrompt) {
          currentStore.dispatch({
            type: 'LOG_INTERACTION',
            payload: {
              type: 'intervention_gate_test',
              taskId: currentSourceIndex,
              timestamp: prompt.ts,
              coverage,
              threshold: QUESTION_THRESHOLD,
              matched: hasTaskQuestion
            }
          })
        }
      }

      const addedDraft = currentStore.state.taskChatDraft
      if (isNewPrompt && addedDraft?.taskId === currentSourceIndex) {
        currentStore.dispatch({
          type: 'TASK_CHAT_DRAFT_SENT',
          payload: {
            taskId: currentSourceIndex,
            timestamp: prompt.ts,
            editedBeforeSend: addedDraft.editedBeforeSend || prompt.content !== addedDraft.insertedText
          }
        })
      }

      let finalResponse
      let replyContent = ''
      let reasoningContent = ''

      const buildParts = () => [
        ...(reasoningContent ? [{ type: 'reasoning', text: reasoningContent }] : []),
        ...(replyContent ? [{ type: 'text', text: replyContent }] : [])
      ]

      for await (const event of requestChatResponseStream(backendMessages, abortSignal, hasTaskQuestion)) {
        if (event.type === 'reasoning') {
          reasoningContent = event.reasoning || `${reasoningContent}${event.delta || ''}`
          yield { content: buildParts() }
        }

        if (event.type === 'delta') {
          replyContent = event.content || `${replyContent}${event.delta || ''}`
          yield { content: buildParts() }
        }

        if (event.type === 'done') {
          finalResponse = event.response
          const message = finalResponse?.choices?.[0]?.message
          reasoningContent = reasoningContent || message?.reasoning || ''
          replyContent = replyContent || message?.content || ''
        }
      }

      if (!finalResponse) {
        finalResponse = {
          choices: [
            {
              index: 0,
              message: { role: 'assistant', content: replyContent, ...(reasoningContent ? { reasoning: reasoningContent } : {}) },
              finish_reason: 'stop'
            }
          ]
        }
      }

      currentStore.dispatch({
        type: 'UPDATE_MESSAGES',
        payload: {
          prompt,
          response: {
            role: 'assistant',
            ...finalResponse,
            render_complete: Date.now(),
            survey_index: currentSourceIndex
          }
        }
      })

      /* Unlock progression only for a fresh prompt AND only if the participant is still on
       * the page where generation started — finishing (or regenerating) after they moved on
       * must not unlock the page they haven't prompted on yet. */
      if (isNewPrompt && sourceIndexRef.current === currentSourceIndex) {
        currentStore.dispatch({ type: 'TOGGLE_CHAT_USED', payload: { value: true } })
      }

      yield {
        content: buildParts()
      }
    }
  }), [])

  const runtimeOptions = useMemo(() => ({
    adapters: enableImages ? { attachments: new SimpleImageAttachmentAdapter() } : undefined
  }), [])

  const runtime = useLocalRuntime(chatModel, runtimeOptions)

  return (
    <div className='flex flex-1 flex-col justify-start items-center h-screen border-l border-[#e5e5e5] bg-[#fafafa]'>
      {ctxStore.state.chatEnabled && (
        <div className='flex justify-center items-center w-full bg-[#fafafa] py-3'>
          <Chip color='success' variant='dot'>AI Assistant</Chip>
        </div>
      )}
      <div className='min-h-0 w-full flex-1'>
        {ctxStore.state.chatEnabled && (
          <AssistantRuntimeProvider runtime={runtime}>
            <Thread />
          </AssistantRuntimeProvider>
        )}
      </div>
    </div>
  )
}

export default ChatView
