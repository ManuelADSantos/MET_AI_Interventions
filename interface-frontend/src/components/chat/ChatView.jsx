import React, { useContext, useMemo, useRef } from 'react'
import { AssistantRuntimeProvider, SimpleImageAttachmentAdapter, useLocalRuntime } from '@assistant-ui/react'
import { Chip } from '@nextui-org/react'
import { store } from '../../scripts/store'
import { requestChatResponse } from '../../scripts/chatService'
import { Thread } from '../thread'

const enableImages = import.meta.env.VITE_ALLOW_IMAGES ? import.meta.env.VITE_ALLOW_IMAGES === 'true' : true

const partText = (part) => {
  if (!part) return ''
  if (part.type === 'text') return part.text || ''
  if (typeof part.text === 'string') return part.text
  return ''
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

const getAssistantReply = (fullRes) => {
  return fullRes?.choices?.[0]?.message?.content || ''
}

const ChatView = ({ sourceIndex }) => {
  const ctxStore = useContext(store)
  const ctxStoreRef = useRef(ctxStore)
  const sourceIndexRef = useRef(sourceIndex)

  ctxStoreRef.current = ctxStore
  sourceIndexRef.current = sourceIndex

  const chatModel = useMemo(() => ({
    async run({ messages, abortSignal }) {
      const currentStore = ctxStoreRef.current
      const currentSourceIndex = sourceIndexRef.current

      if (currentStore.state.displayChatOnboarding) {
        currentStore.dispatch({ type: 'DISMISS_ONBOARDING' })
      }

      const backendMessages = messages
        .filter((message) => ['user', 'assistant'].includes(message.role))
        .map(toBackendMessage)

      const newestUserMessage = [...backendMessages].reverse().find((message) => message.role === 'user')
      const prompt = {
        role: 'user',
        content: newestUserMessage?.content || '',
        image: newestUserMessage?.image,
        ts: Date.now(),
        task: currentSourceIndex
      }

      const res = await requestChatResponse(backendMessages, abortSignal)
      if (res.error) {
        throw new Error(res.error)
      }

      const replyContent = getAssistantReply(res)

      currentStore.dispatch({
        type: 'UPDATE_MESSAGES',
        payload: {
          prompt,
          response: {
            role: 'assistant',
            ...res,
            render_complete: Date.now(),
            survey_index: currentSourceIndex
          }
        }
      })

      currentStore.dispatch({ type: 'TOGGLE_CHAT_USED', payload: { value: true } })

      return {
        content: [{ type: 'text', text: replyContent }]
      }
    }
  }), [])

  const runtimeOptions = useMemo(() => ({
    adapters: enableImages ? { attachments: new SimpleImageAttachmentAdapter() } : undefined
  }), [])

  const runtime = useLocalRuntime(chatModel, runtimeOptions)

  return (
    <div className='flex flex-1 flex-col justify-start items-center w-3/6 h-screen bg-white'>
      {ctxStore.state.chatEnabled && (
        <div className='flex justify-center items-center w-full py-3'>
          <Chip color='success' variant='dot'>ChatGPT</Chip>
        </div>
      )}
      <div className='min-h-0 w-full flex-1'>
        {ctxStore.state.chatEnabled && (
          <AssistantRuntimeProvider runtime={runtime}>
            <Thread allowAttachments={enableImages} />
          </AssistantRuntimeProvider>
        )}
      </div>
    </div>
  )
}

export default ChatView
