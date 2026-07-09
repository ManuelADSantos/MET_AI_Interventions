import LikertQuestion from './LikertQuestion'
import OptionQuestion from './OptionQuestion'
import SliderQuestion from './SliderQuestion'
import { Input, Textarea } from '@nextui-org/react'
import { useController } from 'react-hook-form'
import RichText from './RichText'

const QuestionWrapper = ({ id, question, formControl }) => {
  const required = question.required !== false
  const { field, fieldState } = useController({
    control: formControl,
    name: id,
    rules: {
      required: {
        value: required,
        message: 'Please answer this question.'
      },
      // Empty values are handled by the required rule above; this lets optional questions skip validation when left blank
      validate: (v) => (v === undefined || v === null || v === '') || validateAnswer(v, question)
    }
  })

  return (
    <div className='my-16'>
      <div className='flex flex-row justify-between items-center mb-4'>
        <h3 className='text-lg font-bold'>{id} - <RichText inline>{question.question}</RichText>{required && <span className='text-red-500'>*</span>}</h3>
      </div>
      {/* Optional helper text shown beneath the question title */}
      {question.subtitle && <p className='text-sm text-default-500 -mt-3 mb-3'>{question.subtitle}</p>}
      {/* Display error if validation rules breached */}
      {fieldState.error && <p className='text-red-500 mb-2 ml-2'>{fieldState.error.message}</p>}
      {/* Render the appropriate component based on question type */}
      {question.type === 'text' && <Input id={id} name={id} className='w-5/6' variant='bordered' type="text" {...field}/>}
      {question.type === 'textarea' && <Textarea id={id} name={id} className='w-5/6' variant='bordered' type="text" minRows={3} maxRows={8} {...field}/>}
      {question.type === 'number' && <Input id={id} name={id} className='w-2/6' variant='bordered' type="number"
        onKeyDown={(e) => (['e', 'E', '+', '.'].includes(e.key) || (e.key === '-' && (question.min ?? 0) >= 0)) && e.preventDefault()}
        {...field}/>}
      {question.type === 'likert' && <LikertQuestion id={id} question={question} field={field} />}
      {question.type === 'option' && <OptionQuestion id={id} question={question} field={field} />}
      {question.type === 'slider' && <SliderQuestion id={id} question={question} field={field}/>}
    </div>
  )
}

/* Returns true when valid, an error message string otherwise. */
const validateAnswer = (v, question) => {
  switch (question.type) {
    case 'text':
      if (v.length < 2) return 'Must be at least 2 characters long.'
      return v.length <= 200 || 'Maximum 200 characters.'
    case 'textarea':
      if (v.length < 2) return 'Must be at least 2 characters long.'
      return v.length <= 400 || 'Maximum 400 characters.'
    case 'number': {
      const min = question.min ?? 0
      const max = question.max ?? 999
      if (isNaN(v)) return 'Please enter a number'
      if (!Number.isInteger(parseFloat(v))) return 'Please enter a rounded number.'
      return (Number(v) >= min && Number(v) <= max) || `Please enter a number between ${min} and ${max}`
    }
    case 'slider':
      return (v >= question.min && v <= question.max) || 'Invalid slider value'
    case 'likert':
      return (v >= question.min && v <= question.max) || 'Invalid value'
    case 'option':
      return question.options.some((o) => o.toLowerCase() === 'other')
        ? true
        : (question.options.includes(v) || 'Please select one')
    default:
      return true
  }
}

export default QuestionWrapper
