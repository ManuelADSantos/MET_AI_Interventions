import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const inlineComponents = {
  p: ({ children }) => <>{children}</>,
  a: ({ children, ...props }) => (
    <a className='text-blue-600 underline underline-offset-2' {...props}>
      {children}
    </a>
  )
}

const blockComponents = {
  p: ({ children }) => <p className='mb-4 leading-relaxed'>{children}</p>,
  a: ({ children, ...props }) => (
    <a className='text-blue-600 underline underline-offset-2' {...props}>
      {children}
    </a>
  ),
  table: ({ children }) => (
    <div className='my-4 w-full overflow-hidden rounded-lg border border-[#d4d4d4]'>
      <table className='w-full table-auto border-separate border-spacing-0'>
        {children}
      </table>
    </div>
  ),
  th: ({ children, align }) => (
    <th
      align={align}
      className='whitespace-normal break-words border-b border-[#c7c7c7] bg-[#f3f4f6] px-3 py-2 text-start align-top text-sm font-semibold text-[#111827] first:rounded-ss-lg last:rounded-se-lg'>
      {children}
    </th>
  ),
  td: ({ children, align }) => (
    <td
      align={align}
      className='whitespace-normal break-words border-b border-l border-[#e5e7eb] px-3 py-2 text-start align-top text-sm first:border-l-0 last:border-r'>
      {children}
    </td>
  ),
  ul: ({ children }) => <ul className='mb-4 ml-8 list-disc'>{children}</ul>,
  ol: ({ children }) => <ol className='mb-4 ml-8 list-decimal'>{children}</ol>,
  li: ({ children }) => <li className='mb-1 leading-relaxed'>{children}</li>,
  code: ({ children }) => (
    <code className='rounded bg-stone-200 px-1 py-0.5 font-mono text-sm'>
      {children}
    </code>
  )
}

const RichText = ({ children, inline = false }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={inline ? inlineComponents : blockComponents}
    >
      {String(children || '')}
    </ReactMarkdown>
  )
}

export default RichText
