import React, { useContext, useState } from 'react'
import { useForm } from 'react-hook-form'
import { store } from '../../../scripts/store'
import { Button, ScrollShadow, Tabs, Tab, Tooltip } from '@nextui-org/react'
import PlainContentWrapper from './PlainContentWrapper'
import QuestionWrapper from './QuestionWrapper'
import RichText from './RichText'

const defaultCopyTemplate = 'Please help me solve this task.\n\n{exerciseText}\n\nRelevant information:\n{tabText}\n\n{copyText}'

const parsePageList = (value) => {
  const pages = new Set()

  String(value)
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean)
    .forEach((part) => {
      const rangeMatch = part.match(/^(\d+)\s*-\s*(\d+)$/)

      if (rangeMatch) {
        const start = parseInt(rangeMatch[1], 10)
        const end = parseInt(rangeMatch[2], 10)
        for (let page = Math.min(start, end); page <= Math.max(start, end); page++) {
          pages.add(page)
        }
        return
      }

      const page = parseInt(part, 10)
      if (!Number.isNaN(page)) {
        pages.add(page)
      }
    })

  return pages
}

const decodeTemplate = (value) => String(value).replace(/\\n/g, '\n')

const copyButtonPages = parsePageList(import.meta.env.VITE_COPY_BUTTON_PAGES || '')
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
  if (['text', 'textarea', 'number', 'likert', 'option', 'slider'].includes(item.type)) {
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
  .filter((item) => ['text', 'textarea', 'number', 'likert', 'option', 'slider'].includes(item.type))
  .map((item) => item.question)
  .filter(Boolean)
  .join('\n\n')

const getOptionsText = (items) => items
  .filter((item) => item.type === 'option' && item.options?.length)
  .map((item) => item.options.map((option, index) => `${String.fromCharCode(65 + index)}. ${option}`).join('\n'))
  .join('\n\n')

const buildCopyText = ({ template, pageTitle, tab, pageTabs, exerciseItems }) => {
  const tabText = tabToText(tab)
  const copyText = tab.copyText || ''
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
        className='mb-4'
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

const TaskPage = ({ taskIndex, sourceIndex, title, items, tabs, next }) => {
  const [submitError, setSubmitError] = useState('')
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

  const exerciseItems = pageTabs.find(
    (tab) => tab.title.toLowerCase() === 'exercise'
  )?.content || pageTabs[0].content

  const shouldShowCopyButton = ctxStore.state.chatEnabled &&
    ctxStore.state.condition === 'ai' &&
    copyButtonPages.has(sourceIndex)

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
        ['text', 'textarea', 'number', 'likert', 'option', 'slider'].includes(c.type)
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

    /* A pretty crude attention check. Just blocks progress until correct. */
    if (taskIndex === parseInt(import.meta.env.VITE_ATTN_CHECK_PAGE)) {
      const pass = []
      const correct = import.meta.env.VITE_ATTN_CHECK_RES.split(',')
      pageResponses[taskIndex].forEach((r) => {
        if (correct.includes(r)) {
          pass.push(true)
        } else {
          pass.push(false)
        }
      })

      if (pass.includes(false)) {
        setSubmitError('Looks like you were not quite paying attention. Please try again.')
        return
      }
    }

    ctxStore.dispatch({ type: 'UPDATE_RESPONSES', payload: {index: sourceIndex, responses: mappedResponses}})
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
      ['text', 'textarea', 'number', 'likert', 'option', 'slider'].includes(c.type)
    )

    return onlyQuestions.indexOf(question) + 1
  }

  const renderContentItem = (item, i) => {
  if (['image', 'paragraph', 'h2', 'h3', 'ul', 'ol'].includes(item.type)) {
    return <PlainContentWrapper key={i} content={item} />
  }

  if (['text', 'textarea', 'number', 'likert', 'option', 'slider'].includes(item.type)) {
    return (
      <QuestionWrapper
        key={i}
        id={`${taskIndex}.${getQuestionIndex(item)}`}
        question={item}
        formControl={control}
      />
    )
  }

  return null
  }

  return (
    <form onSubmit={handleSubmit(onSubmit, showSubmitError)} className='flex flex-1 flex-col justify-between items-start w-full h-full' autoComplete='off'>
      {/* Display page contents */}
      <div className='flex flex-1 flex-col justify-start items-start w-full overflow-auto'>
        <h1 className='text-4xl font-bold mb-4'><RichText inline>{title}</RichText></h1>
        <ScrollShadow className='pb-4 w-full'>
        {hasMultipleTabs ? (
          <Tabs aria-label="Task tabs" variant="underlined">
            {pageTabs.map((tab) => (
              <Tab key={tab.title} title={tab.title}>
                <div className="pt-6">
                  {shouldShowCopyButton && (
                    <div className='flex w-full justify-end'>
                      <TabCopyButton
                        text={buildCopyText({
                          template: copyTemplate,
                          pageTitle: title,
                          tab,
                          pageTabs,
                          exerciseItems
                        })}
                      />
                    </div>
                  )}
                  {tab.content.map(renderContentItem)}
                </div>
              </Tab>
            ))}
          </Tabs>
        ) : (
          <>
            {shouldShowCopyButton && (
              <div className='flex w-full justify-end'>
                <TabCopyButton
                  text={buildCopyText({
                    template: copyTemplate,
                    pageTitle: title,
                    tab: pageTabs[0],
                    pageTabs,
                    exerciseItems
                  })}
                />
              </div>
            )}
            {pageTabs[0].content.map(renderContentItem)}
          </>
  )}
</ScrollShadow>
      </div>
      {/* Display contextual info + submit button */}
      <div className='w-full flex flex-row justify-between items-center mt-4'>
        {/* Display form error if some fields are invalid */}
        <p className='text-red-500 font-bold'>
          {submitError.length > 0 && <i className="bi bi-exclamation-triangle text-xl mr-2"></i>}
          {submitError}
        </p>
        {/* Display instruction to use chat if not used on this page yet */}
        <p className={`text-emerald-500 font-bold -mr-16 ${(ctxStore.state.chatEnabled && !ctxStore.state.chatUsedOnPage) ? '' : 'hidden'}`}>
          <i className='bi bi-info-circle text-xl mr-2'></i>
          Prompt AI on the right at least once before continuing.
        </p>
        {/* Submit button (hidden if chat has not been used) */}
        <Button 
          className={(ctxStore.state.chatEnabled && !ctxStore.state.chatUsedOnPage) ? 'invisible' : ''} 
          isDisabled={ctxStore.state.chatEnabled && !ctxStore.state.chatUsedOnPage} 
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
