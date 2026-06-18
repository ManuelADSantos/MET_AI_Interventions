import React from 'react'

const renderFormattedText = (text) => {
  const lines = String(text).split('\n')

  return lines.flatMap((line, lineIndex) => {
    const parts = line.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g)
    const formattedParts = parts.map((part, i) => {
      const key = `${lineIndex}.${i}`

      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={key}>{part.slice(2, -2)}</strong>
      }

      if (part.startsWith('*') && part.endsWith('*')) {
        return <em key={key}>{part.slice(1, -1)}</em>
      }

      return part
    })

    return lineIndex === lines.length - 1
      ? formattedParts
      : [...formattedParts, <br key={`${lineIndex}.br`} />]
  })
}

const RichText = ({ children }) => {
  return <>{renderFormattedText(children)}</>
}

export { renderFormattedText }
export default RichText
