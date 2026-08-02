import { useContext } from 'react'
import { store } from '../../scripts/store'
import { conditionHasChat } from '../../scripts/conditions'
import TaskPage from './questions/TaskPage'
import DonePage from './DonePage'
import ReflectionPage from './ReflectionPage'

const devMode = import.meta.env.VITE_DEV_MODE === 'true'

const TaskView = ({ tasks }) => {
  const {dispatch, state} = useContext(store)

  const handleNextPage = () => {
    let nextTaskSourceIndex = tasks[state.taskIndex].sourceIndex + 1

    if (tasks[state.taskIndex + 1]) {
      nextTaskSourceIndex = tasks[state.taskIndex + 1].sourceIndex
    }

    dispatch({ type: 'UPDATE_TASK_TIMESTAMP', payload: {index: nextTaskSourceIndex, ts: Date.now()}})
    const nextChat = conditionHasChat(state.condition) && tasks[state.taskIndex + 1]?.chatEnabled
    dispatch({ type: 'NEXT_TASK', payload: { chatEnabled: nextChat } })
  }

  return (
    <div className='flex flex-1 flex-col justify-start items-center w-3/6 h-screen p-10 bg-stone-100'>
      {state.taskIndex < tasks.length
        ? <>
            <div className='w-full mb-2'>
              {devMode
                ? <>
                    <input type='range' className='w-full accent-blue-500 h-1.5 cursor-pointer' min={0} max={tasks.length - 1} value={state.taskIndex} onChange={(e) => { const i = Number(e.target.value); dispatch({ type: 'SET_TASK_INDEX', payload: { index: i, chatEnabled: conditionHasChat(state.condition) && tasks[i]?.chatEnabled } }) }} />
                    <p className='text-xs text-blue-500 text-center mt-1'>[DEV] {state.taskIndex + 1} / {tasks.length} — {state.condition}</p>
                  </>
                : <>
                    <div className='w-full bg-stone-200 rounded-full h-1.5'>
                      <div className='bg-stone-500 h-1.5 rounded-full transition-all duration-300' style={{ width: `${((state.taskIndex + 1) / tasks.length) * 100}%` }} />
                    </div>
                    <p className='text-xs text-stone-400 mt-1 text-right'> </p>
                  </>
              }
            </div>
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
        /* ponytail: reflection gets one extra page after the last task; every other
         * condition falls straight through to DonePage exactly as before */
        : state.condition === 'reflection' && state.taskIndex === tasks.length
          ? <ReflectionPage
              sourceIndex={tasks[tasks.length - 1].sourceIndex + 1}
              next={() => dispatch({ type: 'NEXT_TASK', payload: {} })}
            />
          : <DonePage />
      }
    </div>
  )
}

export default TaskView
