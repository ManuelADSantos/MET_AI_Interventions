import { useMemo, useState } from 'react'
import { Input } from '@nextui-org/react'
import RichText from './RichText'

const optionRadioStyle = 'mr-2 appearance-none box-border border-2 border-stone-300 shadow-inner w-8 h-8 min-w-8 min-h-8 max-w-8 max-h-8 rounded-full checked:border-stone-700 checked:shadow-xl checked:border-8 checked:box-border'
const optionCheckboxStyle = 'mr-2 appearance-none box-border border-2 border-stone-300 shadow-inner w-8 h-8 min-w-8 min-h-8 max-w-8 max-h-8 rounded-md checked:border-stone-700 checked:shadow-xl checked:border-8 checked:box-border'

const OptionQuestion = ({ id, question, field, multi }) => {
  // ponytail: option ending with '*' or '*placeholder' or named 'other' triggers a free-text input
  const otherRaw = question.options.find((o) => o.toLowerCase() === 'other' || /\*/.test(o))
  const hasOther = !!otherRaw
  const otherLabel = otherRaw?.includes('*') ? otherRaw.split('*')[0] : 'Other'
  const otherPlaceholder = otherRaw?.includes('*') ? (otherRaw.split('*')[1] || '') : ''
  const options = useMemo(
    () => question.options.filter((o) => o !== otherRaw),
    [question.options]
  )

  // --- Single-select (radio) state ---
  const fieldValue = field.value ?? (multi ? [] : '')
  const isOtherValue = !multi && hasOther && fieldValue !== '' && !options.includes(fieldValue)
  const [other, setOther] = useState(isOtherValue ? fieldValue : '')
  const [otherSelected, setOtherSelected] = useState(isOtherValue)

  // --- Multi-select (checkbox) helpers ---
  const selected = multi ? (Array.isArray(fieldValue) ? fieldValue : []) : null
  const [otherMulti, setOtherMulti] = useState('')
  const [otherCheckedMulti, setOtherCheckedMulti] = useState(false)

  const toggleCheckbox = (value) => {
    const next = selected.includes(value) ? selected.filter((v) => v !== value) : [...selected, value]
    field.onChange(next)
  }

  const toggleOtherCheckbox = () => {
    if (otherCheckedMulti) {
      setOtherCheckedMulti(false)
      field.onChange(selected.filter((v) => options.includes(v)))
    } else {
      setOtherCheckedMulti(true)
      field.onChange([...selected.filter((v) => options.includes(v)), otherMulti])
    }
  }

  const handleOtherMultiInput = (e) => {
    setOtherMulti(e.target.value)
    field.onChange([...selected.filter((v) => options.includes(v)), e.target.value])
  }

  // --- Single-select handlers ---
  const handleOtherInput = (e) => {
    setOther(e.target.value)
    if (otherSelected) field.onChange(e.target.value)
  }

  const handleSelectOption = (value, isOther) => {
    setOtherSelected(isOther)
    field.onChange(value)
  }

  if (multi) {
    return (
      <div className='my-4'>
        <fieldset style={{border: 'none'}} name={id}>
          {options.map((o, i) =>
            <div key={i} className='mb-3 flex flex-row justify-start items-center'>
              <input
                className={optionCheckboxStyle}
                type='checkbox'
                name={id}
                id={`${id}_${i}`}
                value={o}
                checked={selected.includes(o)}
                onChange={() => toggleCheckbox(o)}
              />
              <label htmlFor={`${id}_${i}`}><RichText inline>{o}</RichText></label>
            </div>
          )}
          {hasOther &&
            <div key='other' className='flex flex-row justify-start items-center'>
              <input
                className={optionCheckboxStyle}
                type='checkbox'
                name={id}
                id={`${id}_other`}
                checked={otherCheckedMulti}
                onChange={toggleOtherCheckbox}
              />
              <label htmlFor={`${id}_other`}>{otherLabel}:</label>
            </div>
          }
        </fieldset>
        {hasOther && otherCheckedMulti &&
          <Input
            className='w-4/6 ml-12 mt-2'
            variant='bordered'
            type="text"
            placeholder={otherPlaceholder}
            value={otherMulti}
            onChange={handleOtherMultiInput}
            isRequired
          />
        }
      </div>
    )
  }

  return (
    <div className='my-4'>
      <fieldset style={{border: 'none'}} name={id}>
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
