import { useContext, useLayoutEffect, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { store } from '../../../scripts/store'
import { Button, Tabs, Tab, Tooltip } from '@nextui-org/react'
import PlainContentWrapper from './PlainContentWrapper'
import QuestionWrapper from './QuestionWrapper'
import RichText from './RichText'


const defaultCopyTemplate = 'Please help me solve this task.\n\n{exerciseText}\n\nRelevant information:\n{tabText}\n\n{copyText}'

const decodeTemplate = (value) => String(value).replace(/\\n/g, '\n')

const copyTemplate = decodeTemplate(import.meta.env.VITE_COPY_BUTTON_TEMPLATE || defaultCopyTemplate)

const contentItemToText = (item) => {
  if (!item) return ''
  if (['paragraph', 'h2', 'h3'].includes(item.type)) return item.text || ''
  if (['ul', 'ol'].includes(item.type)) {
    return (item.items || []).map((listItem, index) => {
      const marker = item.type === 'ol' ? `${index + 1}.` : '-'
      return `${marker} ${listItem}`
    }).join('\n')
  }
  if (['text', 'textarea', 'number', 'likert', 'option', 'checkbox', 'slider'].includes(item.type)) {
    const options = item.options?.length ? `\n${item.options.map((option, index) => `${String.fromCharCode(65 + index)}. ${option}`).join('\n')}` : ''
    return `${item.question || ''}${options}`
  }
  return ''
}

const tabToText = (tab) => (tab?.content || [])
  .map(contentItemToText)
  .filter(Boolean)
  .join('\n\n')

const getQuestionText = (items) => items
  .filter((item) => ['text', 'textarea', 'number', 'likert', 'option', 'checkbox', 'slider'].includes(item.type))
  .map((item) => item.question)
  .filter(Boolean)
  .join('\n\n')

const getOptionsText = (items) => items
  .filter((item) => (item.type === 'option' || item.type === 'checkbox') && item.options?.length)
  .map((item) => item.options.map((option, index) => `${String.fromCharCode(65 + index)}. ${option}`).join('\n'))
  .join('\n\n')

const buildCopyText = ({ template, pageTitle, tab, pageTabs, exerciseItems }) => {
  const tabText = tabToText(tab)
  // ponytail: fall back to visible tab text when no :::copy block exists
  const copyText = tab.copyText || tabText
  const allCopyText = pageTabs
    .map((pageTab) => pageTab.copyText)
    .filter(Boolean)
    .join('\n\n')
  const exerciseText = exerciseItems.map(contentItemToText).filter(Boolean).join('\n\n')
  const allTabsText = pageTabs
    .map((pageTab) => `${pageTab.title}\n${tabToText(pageTab)}`)
    .join('\n\n')

  return template
    .replaceAll('{title}', pageTitle)
    .replaceAll('{tabTitle}', tab.title)
    .replaceAll('{tabText}', tabText)
    .replaceAll('{exerciseText}', exerciseText)
    .replaceAll('{allTabsText}', allTabsText)
    .replaceAll('{copyText}', copyText)
    .replaceAll('{allCopyText}', allCopyText)
    .replaceAll('{questionText}', getQuestionText(exerciseItems))
    .replaceAll('{optionsText}', getOptionsText(exerciseItems))
}

const buildTaskChatDraft = ({ pageTitle, pageTabs, exerciseItems }) => {
  const scenarioTab = pageTabs.find((tab) => tab.title.toLowerCase() === 'scenario')
  const answerIndex = exerciseItems.findIndex((item) => item.type === 'option' || item.type === 'checkbox')
  if (!scenarioTab || answerIndex < 0) return ''

  const scenarioText = scenarioTab.copyText || tabToText(scenarioTab)
  const questionText = exerciseItems
    .slice(0, answerIndex + 1)
    .map(contentItemToText)
    .filter(Boolean)
    .join('\n\n')

  return `${pageTitle}\n\nScenario:\n${scenarioText}\n\nQuestion and answer options:\n${questionText}`
}

const TabCopyButton = ({ text }) => {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <Tooltip className="p-2" content={copied ? 'Copied' : 'Copy to clipboard'}>
      <Button
        className='shrink-0'
        color='default'
        variant='faded'
        disableRipple='true'
        onClick={handleCopy}
        isIconOnly
      >
        <i className={`bi ${copied ? 'bi-clipboard-check text-emerald-700' : 'bi-copy text-stone-500'} text-xl`}></i>
      </Button>
    </Tooltip>
  )
}

const TaskPage = ({ taskIndex, sourceIndex, title, items, tabs, next, isLast, requireAiPrompt }) => {
  const [submitError, setSubmitError] = useState('')
  const [taskAddedToChat, setTaskAddedToChat] = useState(false)
  const ctxStore = useContext(store)
  const { handleSubmit, control } = useForm({
    mode: 'onSubmit'
  })

  const pageTabs = tabs || [
    {
      title: 'Exercise',
      content: items
    }
  ]

  const hasMultipleTabs = pageTabs.length > 1
  const [selectedTabKey, setSelectedTabKey] = useState(pageTabs[0].title)
  const selectedTab = pageTabs.find((tab) => tab.title === selectedTabKey) || pageTabs[0]
  const scrollContainerRef = useRef(null)
  const tabScrollPositionsRef = useRef({})

  const exerciseItems = pageTabs.find(
    (tab) => tab.title.toLowerCase() === 'exercise'
  )?.content || pageTabs[0].content
  const primaryAnswerItem = exerciseItems.find((item) => item.type === 'option' || item.type === 'checkbox')
  const taskChatText = buildTaskChatDraft({ pageTitle: title, pageTabs, exerciseItems })
  const canAddTaskToChat = ctxStore.state.chatEnabled && !!primaryAnswerItem && !!taskChatText

  const handleAddTaskToChat = () => {
    window.dispatchEvent(new CustomEvent('study:add-task-to-chat', {
      detail: {
        text: taskChatText,
        focusOnly: taskAddedToChat,
        onInserted: taskAddedToChat ? undefined : (insertedText) => {
          ctxStore.dispatch({
            type: 'TASK_ADDED_TO_CHAT',
            payload: { taskId: sourceIndex, timestamp: Date.now(), insertedText }
          })
          setTaskAddedToChat(true)
        }
      }
    }))
  }

  useLayoutEffect(() => {
    const scrollContainer = scrollContainerRef.current
    if (!scrollContainer) return

    const savedScrollTop = tabScrollPositionsRef.current[selectedTabKey] ?? 0
    scrollContainer.scrollTop = savedScrollTop
  }, [selectedTabKey])

  const handleTabSelectionChange = (key) => {
    const nextKey = String(key)
    if (scrollContainerRef.current) {
      tabScrollPositionsRef.current[selectedTabKey] = scrollContainerRef.current.scrollTop
    }
    setSelectedTabKey(nextKey)
  }

  // ponytail: copy button shows on all chat-enabled pages unless :::no-copy
  const shouldShowCopyButton = ctxStore.state.chatEnabled &&
    !selectedTab.copyDisabled

  // ponytail: dev mode lifts all restrictions
  const isDevMode = import.meta.env.VITE_DEV_MODE === 'true'
  // The last page's Next completes the study — never gate it behind an AI prompt
  const shouldRequireAiPrompt = !isDevMode && requireAiPrompt &&
    !isLast &&
    ctxStore.state.chatEnabled

  const onSubmit = (pageResponses) => {    
    const mappedResponses = {}
    /* Since we're using hook form at this level instead of in a child component, it also keeps track of
    * ALL of the responses instead ofjust the ones filled in to the currently visible questionnaire. 
    * This is why we need to use the visible task index to access the contents of the currently visible questionnaire.
    */
    if (pageResponses[taskIndex]) {
      /* The form hook returns form contents as a list by default, but we want to connect the responses to question IDs. 
      * Because these will be logged, we should map them to the source task index so we can compare between-participant 
      * responses later.
      */
      const questionItems = exerciseItems.filter((c) =>
        ['text', 'textarea', 'number', 'likert', 'option', 'checkbox', 'slider'].includes(c.type)
      )
      pageResponses[taskIndex].forEach((r, i) => {
        if (r !== undefined && r !== null) {
          const questionItem = questionItems[i - 1]
          mappedResponses[`${sourceIndex}.${i}`] = {
            question: questionItem?.question || '',
            answer: r
          }
        }
      })
    }

    /* Attention checks no longer block progression: answers are recorded like any other
     * response and checked offline during analysis. */
    ctxStore.dispatch({
      type: 'UPDATE_RESPONSES',
      payload: {
        index: sourceIndex,
        responses: mappedResponses
      }
    })
    next()
  }

  const showSubmitError = () => {
    setSubmitError('Please respond to all questions before proceeding.')
  }

  /**
   * Since all page contents are included in items, if we want to know
   * the ordinal of a question on a page, we'll need to do some filtering.
   * 
   * This is ONLY used to render the participant-facing question number, not what is logged (see onSubmit above)!
   * */ 
  const getQuestionIndex = (question) => {
    const onlyQuestions = exerciseItems.filter((c) =>
      ['text', 'textarea', 'number', 'likert', 'option', 'checkbox', 'slider'].includes(c.type)
    )

    return onlyQuestions.indexOf(question) + 1
  }

  const renderContentItem = (item, i) => {
  if (['image', 'paragraph', 'h2', 'h3', 'ul', 'ol'].includes(item.type)) {
    return <PlainContentWrapper key={i} content={item} />
  }

  if (['text', 'textarea', 'number', 'likert', 'option', 'checkbox', 'slider'].includes(item.type)) {
    return (
      <div key={i} className='w-full'>
        {canAddTaskToChat && item === primaryAnswerItem && (
          <Tooltip content='Adds the scenario and current question to the chat input. You can edit it before sending.'>
            <Button
              type='button'
              size='m' 
              borderWeight='light'
              className='mt-2 mb-2'
              variant='flat' 
              onClick={handleAddTaskToChat}
            >
              <i className={`bi ${taskAddedToChat ? 'bi-clipboard-check text-emerald-700' : 'bi-copy text-stone-500'}`}></i>
              {taskAddedToChat ? 'Pasted to chat' : 'Copy-paste task & scenario to chat'}
            </Button>
          </Tooltip>
        )}
        <QuestionWrapper
          id={`${taskIndex}.${getQuestionIndex(item)}`}
          question={item}
          formControl={control}
        />
      </div>
    )
  }

  return null
  }

  return (
    <form onSubmit={handleSubmit(onSubmit, showSubmitError)} className='flex flex-1 flex-col justify-between items-start w-full min-h-0' autoComplete='off'>
      {/* Display page contents */}
      <div className='flex flex-1 flex-col justify-start items-start w-full min-h-0 overflow-auto'>
        <h1 className='text-4xl font-bold mb-4'><RichText inline>{title}</RichText></h1>
        {(hasMultipleTabs || shouldShowCopyButton) && (
          <div className='mb-4 flex w-full items-center justify-between gap-4'>
            {hasMultipleTabs ? (
              <Tabs
                aria-label="Task tabs"
                selectedKey={selectedTabKey}
                onSelectionChange={handleTabSelectionChange}
                variant="underlined"
                className='min-w-0 flex-1'
                classNames={{
                  panel: 'hidden'
                }}
              >
                {pageTabs.map((tab) => (
                  <Tab key={tab.title} title={tab.title} />
                ))}
              </Tabs>
            ) : (
              <div />
            )}
            {shouldShowCopyButton && (
              <TabCopyButton
                text={buildCopyText({
                  template: copyTemplate,
                  pageTitle: title,
                  tab: selectedTab,
                  pageTabs,
                  exerciseItems
                })}
              />
            )}
          </div>
        )}
        <div ref={scrollContainerRef} className='w-full flex-1 overflow-y-auto pb-4'>
          {selectedTab.content.map(renderContentItem)}
        </div>
      </div>
      {/* Display contextual info + submit button */}
      <div className='w-full flex flex-row justify-between items-center mt-4'>
        {/* Display form error if some fields are invalid */}
        <p className='text-red-500 font-bold'>
          {submitError.length > 0 && <i className="bi bi-exclamation-triangle text-xl mr-2"></i>}
          {submitError}
        </p>
        {/* Display instruction to use chat if not used on this page yet */}
        <p className={`text-emerald-500 font-bold -mr-16 ${(shouldRequireAiPrompt && !ctxStore.state.chatUsedOnPage) ? '' : 'hidden'}`}>
          <i className='bi bi-info-circle text-xl mr-2'></i>
          Prompt AI on the right at least once before continuing.
        </p>
        {/* Submit button (hidden if chat has not been used) */}
        <Button
          className={(shouldRequireAiPrompt && !ctxStore.state.chatUsedOnPage) ? 'invisible' : ''}
          isDisabled={shouldRequireAiPrompt && !ctxStore.state.chatUsedOnPage}
          color='primary'
          type='submit'
        >
          Next
        </Button>
      </div>
    </form>
  )
}

export default TaskPage
