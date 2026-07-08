import { useContext, useEffect, useState } from "react"
import { store } from "./scripts/store"
import { checkParticipation } from "./scripts/dbService"
import TaskView from './components/tasks/TaskView'
import ChatView from "./components/chat/ChatView"
import { Button, Card, CardBody, Input, CardHeader } from '@nextui-org/react'

const urlParams = new URLSearchParams(window.location.search)
const urlPid = urlParams.get('PROLIFIC_PID')

const App = ({ condition, tasks, directStartPid }) => {
  const [idGiven, setIdGiven] = useState(false)
  const [idError, setIdError] = useState('')
  const ctxStore = useContext(store)

  const startStudy = (pid) => {
    ctxStore.dispatch({type: 'UPDATE_ID', payload: {id: pid}})
    ctxStore.dispatch({type: 'UPDATE_CONDITION', payload: {condition}})
    // Stamp the first page's entry time; later pages are stamped on navigation in TaskView
    ctxStore.dispatch({type: 'UPDATE_TASK_TIMESTAMP', payload: {index: tasks[0].sourceIndex, ts: Date.now()}})
    ctxStore.dispatch({type: 'NEXT_TASK'})
    setIdGiven(true)
  }

  const submitId = async (pid) => {
    if (import.meta.env.VITE_DEV_MODE === 'true') {
      startStudy(pid)
      return
    }

    if (pid.trim().length < 16) {
      setIdError('Please enter your Prolific ID.')
      return
    }

    const res = await checkParticipation(pid)
    if (!res.error) {
      startStudy(pid)
    } else {
      setIdError(res.error)
    }
  }

  useEffect(() => {
    if (directStartPid) { startStudy(directStartPid); return }
    if (urlPid) submitId(urlPid)
  }, [])

  const handleIdSubmit = (e) => {
    e.preventDefault()
    submitId(e.target[0].value)
  }

  return (
    <>
      {!idGiven 
      ? <div className='flex justify-center items-center h-screen bg-neutral-100'>
        <Card className='p-2' isBlurred shadow='2xl'>
          <CardHeader className="flex gap-3">
          <p className='text-2m font'>Please enter your Prolific ID</p>
          </CardHeader>
          <CardBody>
            
          <form onSubmit={handleIdSubmit}> 
            <div className="flex gap-4">
            <Input  type="text" maxLength={64} label="ID" labelPlacement='outside-left' placeholder='e.g. 0123456789' isInvalid={idError.length > 0} errorMessage={idError && idError} onClear={() => {}}/>
            <Button type="submit" color="primary" variant="solid">Submit</Button>
            </div>
          </form>
          
          </CardBody>
        </Card>
      </div>
      
      : <>
        <div className='flex flex-1 flex-row h-screen'>
          <TaskView tasks={tasks} />
          {condition !== 'no-ai' && <ChatView sourceIndex={
            tasks[ctxStore.state.taskIndex]
            ? tasks[ctxStore.state.taskIndex].sourceIndex
            : tasks[ctxStore.state.taskIndex - 1].sourceIndex
          } />}
        </div>
      </>
      }
    </>
  )
}

export default App
