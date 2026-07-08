import { Slider } from '@nextui-org/react'

const SliderQuestion = ({id, question, field}) => {
  const midpoint = (question.max + question.min) / 2
  const hasValue = field.value !== undefined && field.value !== null && field.value !== ''
  const sliderValue = hasValue ? Number(field.value) : midpoint
  // Enabled via `$slider; min; max; low; high; tooltip` (or `tooltip%` for a percent suffix)
  const tooltipParam = (question.additionalParams || []).find((p) => /^tooltip%?$/.test(p))

  return (
    <div className='flex flex-row justify-center items-center mx-16'>
      <span>{question.minLabel}</span>
      <Slider
        id={id}
        name={id}
        className='mx-8 max-w-md'
        step={1}
        color='foreground'
        label=''
        minValue={question.min}
        maxValue={question.max}
        value={sliderValue}
        fillOffset={sliderValue}
        hideThumb={!hasValue}
        onChange={(value) => {
          field.onChange(value)
        }}
        inputRef={field.ref}
        showTooltip={!!tooltipParam}
        tooltipValueFormatOptions={tooltipParam === 'tooltip%' ? { style: 'unit', unit: 'percent' } : undefined}
      />
      <span>{question.maxLabel}</span>
    </div>
  )
}

export default SliderQuestion
