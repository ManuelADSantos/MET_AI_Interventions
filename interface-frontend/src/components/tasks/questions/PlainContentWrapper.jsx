import React from 'react'
import RichText from './RichText'

const PlainContentWrapper = ({ content }) => {
  return (
    <>
      {content.type === 'paragraph' && <p className='mb-4'><RichText>{content.text}</RichText></p> }
      {content.type === 'image' && <img className='rounded-none w-max-full h-max-64 my-2' src={content.url}></img>}
      {content.type === 'h2' && <h2 className='mt-6 mb-4 text-3xl font-semibold'><RichText>{content.text}</RichText></h2>}
      {content.type === 'h3' && <h3 className='mb-2 mt-4 text-xl font-medium'><RichText>{content.text}</RichText></h3>}
      {content.type === 'ul' && <ul className='list-disc ml-8 mb-4'>{content.items.map((item, i) => <li key={i}><RichText>{item}</RichText></li>)}</ul>}
      {content.type === 'ol' && <ol className='list-decimal ml-8 mb-4'>{content.items.map((item, i) => <li key={i}><RichText>{item}</RichText></li>)}</ol>}
    </>
  )
}

export default PlainContentWrapper
