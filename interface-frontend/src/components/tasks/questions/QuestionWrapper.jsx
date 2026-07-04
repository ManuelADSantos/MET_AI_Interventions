import LikertQuestion from './LikertQuestion'
import OptionQuestion from './OptionQuestion'
import SliderQuestion from './SliderQuestion'
import { Input, Textarea } from '@nextui-org/react'
import { useController } from 'react-hook-form'
import RichText from './RichText'

const QuestionWrapper = ({ id, question, formControl }) => {
  const { field, fieldState } = useController({ 
    control: formControl, 
    name: id, 
    rules: {
      required: {
        value: true, 
        message: 'Please answer this question.'
      }, 
      ...getValidationRules(question) // All fields are required. Get additional rules based on question type.
    }
  })

  return (
    <div className='my-16'>
      <div className='flex flex-row justify-between items-center mb-8'>
        <h3 className='text-lg font-bold'>{id} - <RichText inline>{question.question}</RichText><span className='text-red-500'>*</span></h3>
      </div>
      {/* Display error if validation rules breached */}
      {fieldState.error && <p className='text-red-500 mb-2 ml-2'>{fieldState.error.message}</p>}
      {/* Render the appropriate component based on question type */}
      {question.type === 'text' && <Input id={id} name={id} className='w-5/6' variant='bordered' type="text" {...field}/>}
      {question.type === 'textarea' && <Textarea id={id} name={id} className='w-5/6' variant='bordered' type="text" minRows={3} maxRows={8} {...field}/>}
      {question.type === 'number' && <Input id={id} name={id} className='w-2/6' variant='bordered' type="number" {...field}/>}
      {question.type === 'likert' && <LikertQuestion id={id} question={question} field={field} />}
      {question.type === 'option' && <OptionQuestion id={id} question={question} field={field} />}
      {question.type === 'slider' && <SliderQuestion id={id} question={question} field={field}/>}
    </div>
  )
}

const getValidationRules = (question) => {
  return ({
    'text': {
      minLength: {value: 2, message: 'Must be at least 2 characters long.'},
      maxLength: {value: 200, message: 'Maximum 200 characters.'}
    },
    'textarea': {
      minLength: {value: 2, message: 'Must be at least 2 characters long.'},
      maxLength: {value: 400, message: 'Maximum 400 characters.'}
    },
    'number': {
      min: {value: 0, message: 'Please enter a number between 0 and 999'},
      max: {value: 999, message: 'Please enter a number between 0 and 999'},
      validate: {
        isNumber: (v) => !isNaN(v) || 'Please enter a number',
        isInteger: (v) => Number.isInteger(parseFloat(v)) || 'Please enter a rounded number.'
      }
    },
    'slider': {
      min: {value: question.min, message: 'Invalid slider value'},
      max: {value: question.max, message: 'Invalid slider value'}
    },
    'likert': {
      min: {value: question.min, message: 'Invalid value'},
      max: {value: question.max, message: 'Invalid value'}
    },
    'option': {
      validate: {
        isValidOption: (v) => question.options.some((o) => o.toLowerCase() === 'other') ? true : (question.options.includes(v) || 'Please select one')
      },
      maxLength: {value: 5001, message: 'Maximum 5001 characters.'}
    }
  }[question.type])
}

export default QuestionWrapper
