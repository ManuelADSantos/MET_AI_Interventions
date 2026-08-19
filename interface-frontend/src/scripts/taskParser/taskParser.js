const parseContentItems = (rawContent) => {
  const rawQuestions = splitQuestionDirectivesFromListChunks(rawContent.split(/(?<!#)#{1}|>/).slice(1))

  const parsedItems = rawQuestions.map((rq) => {
    if (rq.startsWith('#')) {
      const subHLevel = rq.match(/(?<!#)#{1,}|>/)[0].length + 1
      return {
        text: String(rq.split(/(?<!#)#{1,}|>/)[1].trim()),
        type: `h${subHLevel}`
      }
    }

    if (rq.trim().startsWith('!')) {
      return {
        url: String(rq.split('(')[1].split(')')[0].trim()),
        type: 'image'
      }
    }

    const list = parseList(rq)
    if (list) {
      return list
    }

    if (rq.split('$').length === 1) {
      return {
        text: String(rq.trim()),
        type: 'paragraph',
        listContinuation: /^\s{2,}/.test(String(rq).replace(/^\r?\n/, ''))
      }
    }

    // A line starting with `~` between the question text and the `$type` directive is an
    // optional subtitle/helper line, shown beneath the question title. Stripped out here so
    // it doesn't get treated as part of the question text or the `$type` params.
    const subtitleMatch = rq.match(/^\s*~\s?(.+)$/m)
    const subtitle = subtitleMatch ? subtitleMatch[1].trim() : undefined
    if (subtitleMatch) {
      rq = rq.replace(subtitleMatch[0], '')
    }

    const [beforeDollar, afterDollar] = [rq.split('$')[0].trim(), rq.split('$')[1].trim()]
    const questionText = beforeDollar
    const rawType = afterDollar.split(';')[0].trim()
    const isRequired = !rawType.endsWith('?')
    const questionType = rawType.replace(/\?$/, '')

    if (questionType === 'likert' || questionType === 'slider') {
      let params = afterDollar.split(';')

      if (params.length < 2) {
        return {
          question: questionText,
          type: questionType,
          required: isRequired,
          subtitle,
          min: 1,
          max: 10,
          minLabel: 'min',
          maxLabel: 'max'
        }
      }

      params = params.slice(1)

      return {
        question: questionText,
        type: questionType,
        required: isRequired,
        subtitle,
        min: parseInt(params[0].trim()),
        max: parseInt(params[1].trim()),
        minLabel: params[2].trim(),
        maxLabel: params[3].trim(),
        additionalParams: [...params.slice(4).map((p) => p.trim())]
      }
    }

    if (questionType === 'option' || questionType === 'checkbox') {
      return {
        question: questionText,
        type: questionType,
        required: isRequired,
        subtitle,
        options: afterDollar.split(';').length > 1
          ? afterDollar.split(';').slice(1).map((o) => o.trim())
          : ['Yes', 'No']
      }
    }

    // `$textarea; 200; 4000` sets a character minimum and maximum. The minimum drives the
    // red/green counter in QuestionWrapper; the default max of 400 is too short for an
    // explain-back answer, so a reflection page raises it.
    if (questionType === 'textarea') {
      const [min, max] = afterDollar.split(';').slice(1).map((p) => parseInt(p.trim()))
      return {
        question: questionText,
        type: questionType,
        required: isRequired,
        subtitle,
        // isFinite, not isNaN: a bare `$textarea` has no params at all, so these are undefined
        // rather than NaN, and Number.isNaN(undefined) is false
        minChars: Number.isFinite(min) ? min : 2,
        maxChars: Number.isFinite(max) ? max : 400
      }
    }

    if (questionType === 'number') {
      const params = afterDollar.split(';').slice(1).map((p) => p.trim())
      const num = (v, fallback) => {
        const n = parseInt(v)
        return Number.isNaN(n) ? fallback : n
      }
      return {
        question: questionText,
        type: questionType,
        required: isRequired,
        subtitle,
        min: num(params[0], 0),
        max: num(params[1], 999)
      }
    }

    return {
      question: questionText,
      type: questionType,
      required: isRequired,
      subtitle
    }
  })

  return mergeConsecutiveMarkdownTables(mergeConsecutiveLists(parsedItems))
}

const splitQuestionDirectivesFromListChunks = (chunks) => {
  return chunks.flatMap((chunk) => {
    const lines = String(chunk).split('\n')
    const firstContentLine = lines.find((line) => line.trim().length > 0)

    if (!firstContentLine || !/^(\s*[-*]\s+|\s*\d+[.)]\s+)/.test(firstContentLine)) {
      return [chunk]
    }

    const directiveIndex = lines.findIndex((line, index) => index > 0 && /^\s*\$/.test(line))

    if (directiveIndex === -1) {
      return [chunk]
    }

    return [
      lines.slice(0, directiveIndex).join('\n'),
      lines.slice(directiveIndex).join('\n')
    ]
  })
}

const parseList = (rawContent) => {
  const lines = String(rawContent)
    .split('\n')
    .map((line) => line.trimEnd())
    .filter((line) => line.trim().length > 0)

  if (lines.length === 0) {
    return undefined
  }

  const firstLine = lines[0].trim()
  const isUnordered = /^[-*]\s+/.test(firstLine)
  const isOrdered = /^\d+[.)]\s+/.test(firstLine)

  if (!isUnordered && !isOrdered) {
    return undefined
  }

  const items = []

  lines.forEach((line) => {
    const trimmedLine = line.trim()
    const isListItem = isOrdered
      ? /^\d+[.)]\s+/.test(trimmedLine)
      : /^[-*]\s+/.test(trimmedLine)

    if (isListItem) {
      items.push(trimmedLine.replace(isOrdered ? /^\d+[.)]\s+/ : /^[-*]\s+/, ''))
      return
    }

    if (items.length > 0) {
      items[items.length - 1] = `${items[items.length - 1]}\n${trimmedLine}`
    }
  })

  return {
    type: isOrdered ? 'ol' : 'ul',
    items
  }
}

const mergeConsecutiveLists = (items) => {
  return items.reduce((merged, item) => {
    const previous = merged[merged.length - 1]

    if (previous && ['ul', 'ol'].includes(previous.type) && item.type === 'paragraph' && item.listContinuation) {
      previous.items[previous.items.length - 1] = `${previous.items[previous.items.length - 1]}\n${item.text}`
      return merged
    }

    if (previous && ['ul', 'ol'].includes(previous.type) && previous.type === item.type) {
      previous.items = [...previous.items, ...item.items]
      return merged
    }

    return [...merged, item]
  }, [])
}

const getMarkdownTableLines = (item) => {
  if (item?.type !== 'paragraph') {
    return []
  }

  return String(item.text || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
}

const isMarkdownTableRow = (line) => /^\|.*\|$/.test(line)

const isMarkdownTableDivider = (line) => {
  const cells = line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((cell) => cell.trim())

  return cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell))
}

const isMarkdownTableBlock = (item) => {
  const lines = getMarkdownTableLines(item)
  return lines.length > 0 && lines.every(isMarkdownTableRow)
}

const hasMarkdownTableDivider = (item) => {
  return getMarkdownTableLines(item).some(isMarkdownTableDivider)
}

const startsWithMarkdownTableDivider = (item) => {
  return isMarkdownTableDivider(getMarkdownTableLines(item)[0] || '')
}

const mergeConsecutiveMarkdownTables = (items) => {
  return items.reduce((merged, item) => {
    const previous = merged[merged.length - 1]

    if (isMarkdownTableBlock(previous) && !hasMarkdownTableDivider(previous) && startsWithMarkdownTableDivider(item)) {
      previous.text = `${previous.text}\n${item.text}`
      return merged
    }

    if (isMarkdownTableBlock(previous) && hasMarkdownTableDivider(previous) && isMarkdownTableBlock(item)) {
      previous.text = `${previous.text}\n${item.text}`
      return merged
    }

    return [...merged, item]
  }, [])
}

const extractCopyBlocks = (rawContent) => {
  const copyBlocks = []
  const copyDisabled = /^\s*:::(copy-disabled|no-copy)\s*$/m.test(String(rawContent))
  const requireAiPrompt = /^\s*:::require-ai-prompt\s*$/m.test(String(rawContent))
  const chatEnabled = /^\s*:::chat-enabled\s*$/m.test(String(rawContent))
  const nextEnabled = /^\s*:{2,3}next\s*$/m.test(String(rawContent))
  // A page marked :::reflect-summary shows the AI's review of the transcript after its questions are
  // submitted, then a Continue button. It is the one part of a reflection that markdown cannot hold.
  const reflectSummary = /^\s*:::reflect-summary\s*$/m.test(String(rawContent))
  // A page marked :::predict-ai hides its questions until the participant predicts whether the AI
  // would solve the task correctly (the manipulation of the prediction condition).
  const predictAi = /^\s*:::predict-ai\s*$/m.test(String(rawContent))
  const content = String(rawContent)
    .replace(/:::copy\s*\n([\s\S]*?)\n:::/g, (_, copyText) => {
    copyBlocks.push(copyText.trim())
    return ''
    })
    .replace(/^\s*:::(copy-disabled|no-copy|require-ai-prompt|chat-enabled|reflect-summary|predict-ai)\s*$/gm, '')
    .replace(/^\s*:{2,3}next\s*$/gm, '')

  return {
    content,
    copyText: copyBlocks.join('\n\n'),
    copyDisabled,
    requireAiPrompt,
    chatEnabled,
    nextEnabled,
    reflectSummary,
    predictAi
  }
}

const parseTabs = (rawPageContent) => {
  if (!rawPageContent.includes(':::tab')) {
    return undefined
  }

  const tabParts = rawPageContent.split(/:::tab\s+/).slice(1)

  return tabParts.map((part) => {
    const firstLineBreak = part.indexOf('\n')
    const title = part.slice(0, firstLineBreak).trim()
    const body = part.slice(firstLineBreak)
    const parsedCopyBlocks = extractCopyBlocks(body)
    const visibleBody = parsedCopyBlocks.content
      .replace(/:::\s*$/, '')
      .trim()

    return {
      title,
      content: parseContentItems(visibleBody),
      copyText: parsedCopyBlocks.copyText,
      copyDisabled: parsedCopyBlocks.copyDisabled,
      nextEnabled: parsedCopyBlocks.nextEnabled
    }
  })
}


const shuffle = (items) => {
  const shuffled = [...items]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

/** A :::reflect-summary page belongs to the page in front of it, so the two shuffle as one unit —
 *  plain shuffling would separate a reflection from the task it asks the participant to recall. */
const shuffleKeepingReflections = (pages) => {
  if (!pages.some((page) => page.reflectSummary)) return shuffle(pages)
  const groups = []
  pages.forEach((page) => {
    if (page.reflectSummary && groups.length) groups[groups.length - 1].push(page)
    else groups.push([page])
  })
  return shuffle(groups).flat()
}

/** Load & parse tasks
 * @param tasks Raw text to parse tasks from.
 * @returns The parsed list of tasks as a JS array.
 *
 * Randomization directives:
 * - `%% RANDOMIZE ... %%` shuffles the pages inside that section
 * - `%% SECTION ... %%` keeps page order but marks the block as a section
 * - a standalone `%% RANDOMIZE_SECTIONS` line shuffles all marked sections
 *   amongst themselves (unmarked content, e.g. an intro, stays in place)
 */
const loadTasks = (tasks, { randomize = true } = {}) => {
  try {
    const lines = String(tasks).split('\n')
    const randomizeSections = randomize && lines.some((l) => l.trim() === '%% RANDOMIZE_SECTIONS')
    const source = lines.filter((l) => l.trim() !== '%% RANDOMIZE_SECTIONS').join('\n')

    // Identify sections (%%)
    const rawSections = source.split('%%').filter((rs) => rs.length !== 0)

    const sections = []
    let pagesSoFar = 0 // Keep track of pages added so far (used to calculate source-based page index below)

    for (const section of rawSections) {
      const header = section.split(/(?<!#)#{1}(?!#)/)[0]
      const isRandom = randomize && header.includes('RANDOMIZE')
      const isSection = isRandom || header.includes('SECTION')

      // Identify pages (#)
      const rawPages = section.split(/(?<!#)#{1}(?!#)/).slice(1)
      
      // Parse pages
      const pages = rawPages.map((rs, pi) => {
        /** pageIndex represents the index of the page within the context of the source file.
        * Weed to use this because of randomized sections where page order may differ from the source,
        * which could mean that different viewers get different page orders. If questions are involved,
        * this would then mean that questionnaire responses get mixed up in logging. 
        * 
        * pi = page index within this section
        * pagesSoFar = number of pages in all previous sections */
        const pageIndex = pi + pagesSoFar
        
        // Parse only the first line as the page title so tab markers stay out of it.
        const pageTitle = rs.split('\n')[0].trim()

        const tabs = parseTabs(rs)
        const parsedPageCopyBlocks = extractCopyBlocks(rs)
        const pageContent = tabs
          ? tabs.find((tab) => tab.title.toLowerCase() === 'exercise')?.content || tabs[0].content
          : parseContentItems(parsedPageCopyBlocks.content)

        return {
          sourceIndex: pageIndex,
          title: pageTitle,
          copyText: parsedPageCopyBlocks.copyText,
          copyDisabled: parsedPageCopyBlocks.copyDisabled,
          requireAiPrompt: parsedPageCopyBlocks.requireAiPrompt,
          chatEnabled: parsedPageCopyBlocks.chatEnabled,
          reflectSummary: parsedPageCopyBlocks.reflectSummary,
          predictAi: parsedPageCopyBlocks.predictAi,
          content: pageContent,
          tabs: tabs || [
            {
              title: 'Exercise',
              content: pageContent,
              copyText: parsedPageCopyBlocks.copyText,
              copyDisabled: parsedPageCopyBlocks.copyDisabled,
              nextEnabled: true
            }
          ]
        }
      })

      pagesSoFar += pages.length // Add the number of pages parsed to the count

      sections.push({
        pages: isRandom ? shuffleKeepingReflections(pages) : pages,
        isSection
      })
    }

    // Shuffle marked sections amongst themselves, leaving unmarked blocks (intro etc.) in place
    if (randomizeSections) {
      const markedIndices = sections.map((s, i) => (s.isSection ? i : -1)).filter((i) => i >= 0)
      const shuffledMarked = shuffle(markedIndices.map((i) => sections[i]))
      markedIndices.forEach((sectionIndex, k) => { sections[sectionIndex] = shuffledMarked[k] })
    }

    return sections.flatMap((s) => s.pages)

  } catch (e) {
    console.log(e)
    return undefined
  }
}

export default loadTasks
