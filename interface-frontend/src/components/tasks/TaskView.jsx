import { useContext } from 'react'
import { store } from '../../scripts/store'
import TaskPage from './questions/TaskPage'
import DonePage from './DonePage'

const TaskView = ({ tasks }) => {
  const {dispatch, state} = useContext(store)
  
  const handleNextPage = () => {
    let nextTaskSourceIndex = tasks[state.taskIndex].sourceIndex + 1

    if (tasks[state.taskIndex + 1]) {
      nextTaskSourceIndex = tasks[state.taskIndex + 1].sourceIndex
    }

    dispatch({ type: 'UPDATE_TASK_TIMESTAMP', payload: {index: nextTaskSourceIndex, ts: Date.now()}})
    dispatch({ type: 'NEXT_TASK' })
  }

  return (
    <div className='flex flex-1 flex-col justify-start items-center w-3/6 h-screen p-10 bg-stone-100'>
      {state.taskIndex < tasks.length
        ? <TaskPage 
            key={state.taskIndex}
            title={tasks[state.taskIndex].title}
            items={tasks[state.taskIndex].content}
            tabs={tasks[state.taskIndex].tabs}
            taskIndex={state.taskIndex}
            sourceIndex={tasks[state.taskIndex].sourceIndex} 
            next={handleNextPage} 
          />
        : <DonePage />
      }
    </div>
  )
}

export default TaskView
