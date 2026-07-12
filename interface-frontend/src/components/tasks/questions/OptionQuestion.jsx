import { useMemo, useState } from 'react'
import { Input } from '@nextui-org/react'
import RichText from './RichText'

const optionRadioStyle = 'mr-2 appearance-none box-border border-2 border-stone-300 shadow-inner w-8 h-8 min-w-8 min-h-8 max-w-8 max-h-8 rounded-full checked:border-stone-700 checked:shadow-xl checked:border-8 checked:box-border'

const OptionQuestion = ({ id, question, field }) => {
  // ponytail: option ending with '*' or '*placeholder' or named 'other' triggers a free-text input
  const otherRaw = question.options.find((o) => o.toLowerCase() === 'other' || /\*/.test(o))
  const hasOther = !!otherRaw
  const otherLabel = otherRaw?.includes('*') ? otherRaw.split('*')[0] : 'Other'
  const otherPlaceholder = otherRaw?.includes('*') ? (otherRaw.split('*')[1] || '') : ''
  const options = useMemo(
    () => question.options.filter((o) => o !== otherRaw),
    [question.options]
  )
  const fieldValue = field.value ?? ''
  const isOtherValue = hasOther && fieldValue !== '' && !options.includes(fieldValue)
  const [other, setOther] = useState(isOtherValue ? fieldValue : '')
  const [otherSelected, setOtherSelected] = useState(isOtherValue)

  /* No effect syncing otherSelected from field.value: selecting "Other" with an empty
   * text box sets the form value to '', which is indistinguishable from "nothing selected"
   * and used to deselect the radio. Local state is the source of truth instead. */
  const handleOtherInput = (e) => {
    setOther(e.target.value)
    /* Only change the currently selected form value if the other option has been selected */
    if (otherSelected) {
      field.onChange(e.target.value)
    }
  }

  const handleSelectOption = (value, isOther) => {
    setOtherSelected(isOther)
    field.onChange(value)
  }

  return (
    <div className='my-4'>
      <fieldset style={{border: 'none'}} name={id}>
        {/* Render all other options first */}
        {options.map((o, i) =>
          <div key={i} className='mb-3 flex flex-row justify-start items-center'>
            <input 
              className={optionRadioStyle}
              type='radio' 
              name={id} 
              id={`${id}_${i}`} 
              value={o} 
              checked={fieldValue === o}
              onChange={(e) => handleSelectOption(e.target.value, false)}
            />
            <label htmlFor={`${id}_${i}`}><RichText inline>{o}</RichText></label>
          </div>
        )}
        {/* If applicable, render "other" option */}
        {hasOther
          && <div key='other' className='flex flex-row justify-start items-center'>
            <input 
              className={optionRadioStyle} 
              type='radio' 
              name={id} 
              id={`${id}_other`}
              value={other}
              checked={otherSelected}
              onChange={() => handleSelectOption(other, true)}
            />
            <label htmlFor={`${id}_other`}>{otherLabel}:</label>
          </div>
        }
      </fieldset>
      {/* Only show text input when the "other" radio is selected */}
      {hasOther && otherSelected
        && <Input
            className='w-4/6 ml-12 mt-2'
            variant='bordered'
            type="text"
            placeholder={otherPlaceholder}
            value={other}
            onChange={handleOtherInput}
            isRequired
          />
      }
    </div>
  )
}

export default OptionQuestion
