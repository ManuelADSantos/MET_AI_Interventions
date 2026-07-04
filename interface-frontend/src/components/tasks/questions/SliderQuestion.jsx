import React, { useState } from 'react'
import { Slider } from '@nextui-org/react'

const SliderQuestion = ({id, question, field}) => {
  const [activated, setActivated] = useState(false)
  const midpoint = (question.max + question.min) / 2

  return (
    <div className='flex flex-row justify-center items-center mx-16'>
      <span>{question.minLabel}</span>
      <Slider
        id={id}
        name={id}
        className='mx-8'
        step={1}
        color='foreground'
        label=''
        minValue={question.min}
        maxValue={question.max}
        defaultValue={midpoint}
        hideThumb={!activated}
        onChange={(value) => {
          if (!activated) setActivated(true)
          field.onChange(value)
        }}
        inputRef={field.ref}
        showTooltip={false}
        classNames={{
          filler: activated ? '' : '!bg-transparent'
        }}
      />
      <span>{question.maxLabel}</span>
    </div>
  )
}

export default SliderQuestion
