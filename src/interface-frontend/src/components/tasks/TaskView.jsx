import { useContext } from 'react'
import { store } from '../../scripts/store'
import { conditionHasChat } from '../../scripts/conditions'
import TaskPage from './questions/TaskPage'
import DonePage from './DonePage'

const devMode = import.meta.env.VITE_DEV_MODE === 'true'

const TaskView = ({ tasks }) => {
  const {dispatch, state} = useContext(store)

  const advance = () => {
    let nextTaskSourceIndex = tasks[state.taskIndex].sourceIndex + 1

    if (tasks[state.taskIndex + 1]) {
      nextTaskSourceIndex = tasks[state.taskIndex + 1].sourceIndex
    }

    dispatch({ type: 'UPDATE_TASK_TIMESTAMP', payload: {index: nextTaskSourceIndex, ts: Date.now()}})
    const nextChat = conditionHasChat(state.condition) && tasks[state.taskIndex + 1]?.chatEnabled
    dispatch({ type: 'NEXT_TASK', payload: { chatEnabled: nextChat } })
  }

  const devMax = tasks.length - 1

  return (
    <div className={`flex flex-col justify-start items-center h-screen p-10 bg-stone-100 ${state.condition === 'alternatives' ? 'w-1/3' : 'flex-1 w-3/6'}`}>
      {devMode && state.taskIndex <= devMax && (
        <div className='w-full mb-2'>
          <input type='range' className='w-full accent-blue-500 h-1.5 cursor-pointer' min={0} max={devMax} value={state.taskIndex} onChange={(e) => { const i = Number(e.target.value); dispatch({ type: 'SET_TASK_INDEX', payload: { index: i, chatEnabled: conditionHasChat(state.condition) && tasks[i]?.chatEnabled } }) }} />
          <p className='text-xs text-blue-500 text-center mt-1'>[DEV] {state.taskIndex + 1} / {devMax + 1} — {state.condition}</p>
        </div>
      )}
      {state.taskIndex < tasks.length
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
              next={advance}
            />
          </>
        : <DonePage />
      }
    </div>
  )
}

export default TaskView
