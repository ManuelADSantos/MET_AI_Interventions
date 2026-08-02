import { useContext, useState } from 'react'
import { store } from '../../scripts/store'
import { conditionHasChat } from '../../scripts/conditions'
import TaskPage from './questions/TaskPage'
import DonePage from './DonePage'
import ReflectionPage from './ReflectionPage'

const devMode = import.meta.env.VITE_DEV_MODE === 'true'

// ponytail: the 12 main exercises are the "Scenario: <name>" pages — the trial is "Trial: ...".
// Same-scenario pages stay contiguous because randomization happens within a section.
const isMainTask = (tasks, i) => !!tasks[i]?.title?.startsWith('Scenario: ')
const endsScenario = (tasks, i) => isMainTask(tasks, i) && tasks[i + 1]?.title !== tasks[i].title

const TaskView = ({ tasks }) => {
  const {dispatch, state} = useContext(store)
  // index of the task page whose reflection is showing, or null
  const [reflectAt, setReflectAt] = useState(null)

  const reflectsAfter = (i) =>
    state.condition === 'reflection-task' ? isMainTask(tasks, i)
      : state.condition === 'reflection-scenario' ? endsScenario(tasks, i)
        : false

  /** sourceIndexes the reflection at page i covers: just that task, or the whole scenario run. */
  const scopeIds = (i) => {
    if (state.condition !== 'reflection-scenario') return [tasks[i].sourceIndex]
    const ids = []
    for (let k = i; k >= 0 && tasks[k].title === tasks[i].title; k -= 1) ids.push(tasks[k].sourceIndex)
    return ids
  }

  const advance = () => {
    let nextTaskSourceIndex = tasks[state.taskIndex].sourceIndex + 1

    if (tasks[state.taskIndex + 1]) {
      nextTaskSourceIndex = tasks[state.taskIndex + 1].sourceIndex
    }

    dispatch({ type: 'UPDATE_TASK_TIMESTAMP', payload: {index: nextTaskSourceIndex, ts: Date.now()}})
    const nextChat = conditionHasChat(state.condition) && tasks[state.taskIndex + 1]?.chatEnabled
    dispatch({ type: 'NEXT_TASK', payload: { chatEnabled: nextChat } })
  }

  const handleNextPage = () => {
    if (reflectsAfter(state.taskIndex)) {
      // kill the chat + transcript for the duration; advance() restores it for the next page
      dispatch({ type: 'SET_CHAT_ENABLED', payload: { value: false } })
      setReflectAt(state.taskIndex)
      return
    }
    advance()
  }

  // ponytail: the end-of-study reflection adds one page past the task list, so dev can scrub
  // one step further. The interstitial variants sit between pages and need no extra slot.
  const devMax = tasks.length - 1 + (state.condition === 'reflection' ? 1 : 0)

  return (
    <div className='flex flex-1 flex-col justify-start items-center w-3/6 h-screen p-10 bg-stone-100'>
      {/* ponytail: dev slider sits outside the page switch so it survives onto the reflection page */}
      {devMode && state.taskIndex <= devMax && (
        <div className='w-full mb-2'>
          <input type='range' className='w-full accent-blue-500 h-1.5 cursor-pointer' min={0} max={devMax} value={state.taskIndex} onChange={(e) => { const i = Number(e.target.value); setReflectAt(null); dispatch({ type: 'SET_TASK_INDEX', payload: { index: i, chatEnabled: conditionHasChat(state.condition) && tasks[i]?.chatEnabled } }) }} />
          <p className='text-xs text-blue-500 text-center mt-1'>[DEV] {state.taskIndex + 1} / {devMax + 1} — {state.condition}{reflectAt !== null ? ' · reflecting' : ''}</p>
        </div>
      )}
      {reflectAt !== null
        ? <ReflectionPage
            key={`reflect-${reflectAt}`}
            storeKey={`reflection.${tasks[reflectAt].sourceIndex}`}
            scopeIds={scopeIds(reflectAt)}
            label={tasks[reflectAt].title.replace(/^Scenario:\s*/, '')}
            next={() => { setReflectAt(null); advance() }}
          />
        : state.taskIndex < tasks.length
        ? <>
            {!devMode && (
              <div className='w-full mb-2'>
                <div className='w-full bg-stone-200 rounded-full h-1.5'>
                  <div className='bg-stone-500 h-1.5 rounded-full transition-all duration-300' style={{ width: `${((state.taskIndex + 1) / tasks.length) * 100}%` }} />
                </div>
                <p className='text-xs text-stone-400 mt-1 text-right'> </p>
              </div>
            )}
            <TaskPage
              key={state.taskIndex}
              title={tasks[state.taskIndex].title}
              items={tasks[state.taskIndex].content}
              tabs={tasks[state.taskIndex].tabs}
              taskIndex={state.taskIndex}
              sourceIndex={tasks[state.taskIndex].sourceIndex}
              requireAiPrompt={tasks[state.taskIndex].requireAiPrompt}
              isLast={state.taskIndex === tasks.length - 1}
              next={handleNextPage}
            />
          </>
        /* ponytail: `reflection` gets one extra page after the last task; every other
         * condition falls straight through to DonePage exactly as before */
        : state.condition === 'reflection' && state.taskIndex === tasks.length
          ? <ReflectionPage
              storeKey='reflection.final'
              final
              next={() => dispatch({ type: 'NEXT_TASK', payload: {} })}
            />
          : <DonePage />
      }
    </div>
  )
}

export default TaskView
