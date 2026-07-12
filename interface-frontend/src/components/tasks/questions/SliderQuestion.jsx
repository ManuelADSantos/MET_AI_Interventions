import { useRef } from 'react'
import { Slider } from '@nextui-org/react'

const SliderQuestion = ({id, question, field}) => {
  const midpoint = Math.round((question.max + question.min) / 2)
  // ponytail: track real user interaction, not mount-triggered onChange
  const touched = useRef(false)
  const hasValue = touched.current || (field.value !== undefined && field.value !== null && field.value !== '')
  const sliderValue = hasValue ? Number(field.value) : midpoint
  // Enabled via `$slider; min; max; low; high; tooltip` (or `tooltip%` for a percent suffix)
  const tooltipParam = (question.additionalParams || []).find((p) => /^tooltip%?$/.test(p))

  return (
    <div className='flex flex-row justify-center items-center mx-16 max-w-2xl self-center'>
      <span className='shrink-0'>{question.minLabel}</span>
      <Slider
        id={id}
        name={id}
        className='mx-8'
        step={1}
        color='foreground'
        label=''
        minValue={question.min}
        maxValue={question.max}
        value={sliderValue}
        fillOffset={sliderValue}
        onChange={(value) => {
          touched.current = true
          field.onChange(value)
        }}
        inputRef={field.ref}
        showTooltip={!!tooltipParam}
        tooltipValueFormatOptions={tooltipParam === 'tooltip%' ? { style: 'unit', unit: 'percent' } : undefined}
        classNames={hasValue ? {} : { thumb: 'opacity-0' }}
      />
      <span className='shrink-0'>{question.maxLabel}</span>
    </div>
  )
}

export default SliderQuestion
