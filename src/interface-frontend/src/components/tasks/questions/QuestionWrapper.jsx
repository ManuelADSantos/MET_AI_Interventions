import LikertQuestion from './LikertQuestion'
import OptionQuestion from './OptionQuestion'
import SliderQuestion from './SliderQuestion'
import { Input, Textarea } from '@nextui-org/react'
import { useController } from 'react-hook-form'
import RichText from './RichText'

const devMode = import.meta.env.VITE_DEV_MODE === 'true'

const QuestionWrapper = ({ id, question, formControl }) => {
  // ponytail: dev mode makes all fields optional for easy navigation
  const required = !devMode && question.required !== false
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
    <div className='my-8'>
      {question.question && <div className='flex flex-row justify-between items-center mb-2'>
        <h3 className='text-lg font-bold'><RichText inline>{question.question}</RichText>{required && <span className='text-red-500'>*</span>}</h3>
      </div>}
      {/* Optional helper text shown beneath the question title */}
      {question.subtitle && <p className='text-sm text-default-500 mb-2'>{question.subtitle}</p>}
      {/* Display error if validation rules breached */}
      {fieldState.error && <p className='text-red-500 mb-2 ml-2'>{fieldState.error.message}</p>}
      {/* Render the appropriate component based on question type */}
      {question.type === 'text' && <Input id={id} name={id} className='w-5/6' variant='bordered' type="text" {...field}/>}
      {question.type === 'textarea' && <>
        <Textarea id={id} name={id} className='w-5/6' variant='bordered' type="text" minRows={3} maxRows={8} {...field}/>
        {/* Only a question that asks for a real minimum gets a counter — red under, green over */}
        {question.minChars > 2 && <p className='text-sm text-stone-500 mt-1'>
          <span className={String(field.value || '').trim().length >= question.minChars ? 'text-emerald-600 font-semibold' : 'text-red-600 font-semibold'}>
            {String(field.value || '').length}
          </span> / {question.minChars} characters minimum
        </p>}
      </>}
      {question.type === 'number' && <Input id={id} name={id} className='w-2/6' variant='bordered' type="number"
        onKeyDown={(e) => (['e', 'E', '+', '.'].includes(e.key) || (e.key === '-' && (question.min ?? 0) >= 0)) && e.preventDefault()}
        {...field}/>}
      {question.type === 'likert' && <LikertQuestion id={id} question={question} field={field} />}
      {question.type === 'option' && <OptionQuestion id={id} question={question} field={field} />}
      {question.type === 'checkbox' && <OptionQuestion id={id} question={question} field={field} multi />}
      {question.type === 'slider' && <SliderQuestion id={id} question={question} field={field}/>}
    </div>
  )
}

/* Returns true when valid, an error message string otherwise. */
const validateAnswer = (v, question) => {
  switch (question.type) {
    case 'text':
      if (v.length < 3) return 'Must be at least 3 characters long.'
      return v.length <= 200 || 'Maximum 200 characters.'
    case 'textarea': {
      const min = question.minChars ?? 2
      const max = question.maxChars ?? 400
      if (v.trim().length < min) return `Must be at least ${min} characters long.`
      return v.length <= max || `Maximum ${max} characters.`
    }
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
      return question.options.some((o) => o.toLowerCase() === 'other' || o.includes('*'))
        ? true
        : (question.options.includes(v) || 'Please select one')
    case 'checkbox':
      return (Array.isArray(v) && v.length > 0) || 'Please select at least one'
    default:
      return true
  }
}

export default QuestionWrapper
