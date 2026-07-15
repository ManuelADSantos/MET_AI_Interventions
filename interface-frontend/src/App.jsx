import { useContext, useEffect, useState } from "react"
import { store } from "./scripts/store"
import { conditionHasChat } from "./scripts/conditions"
import { checkParticipation } from "./scripts/dbService"
import { mintChatToken } from "./scripts/chatService"
import TaskView from './components/tasks/TaskView'
import ChatView from "./components/chat/ChatView"
import { Button, Card, CardBody, Input, CardHeader } from '@nextui-org/react'

const urlParams = new URLSearchParams(window.location.search)
const urlPid = urlParams.get('PROLIFIC_PID')

const App = ({ condition, tasks, directStartPid }) => {
  const [idGiven, setIdGiven] = useState(false)
  const [idError, setIdError] = useState('')
  const ctxStore = useContext(store)

  if (!tasks?.length) return <div className='flex justify-center items-center h-screen bg-neutral-100'><p className='text-red-500 font-bold'>Unknown condition "{condition}". Check the URL.</p></div>

  const startStudy = (pid) => {
    // Registers the session server-side (binds pid→condition) and warms the chat token;
    // chatService re-mints on demand if this fails
    sessionStorage.setItem('pid', pid)
    sessionStorage.setItem('condition', condition)
    mintChatToken().catch(() => {})
    ctxStore.dispatch({type: 'UPDATE_ID', payload: {id: pid}})
    ctxStore.dispatch({type: 'UPDATE_CONDITION', payload: {condition}})
    // Stamp the first page's entry time; later pages are stamped on navigation in TaskView
    ctxStore.dispatch({type: 'UPDATE_TASK_TIMESTAMP', payload: {index: tasks[0].sourceIndex, ts: Date.now()}})
    ctxStore.dispatch({type: 'NEXT_TASK', payload: {chatEnabled: conditionHasChat(condition) && tasks[0]?.chatEnabled}})
    setIdGiven(true)
  }

  const submitId = async (pid) => {
    if (import.meta.env.VITE_DEV_MODE === 'true') {
      startStudy(pid || `dev-${Date.now()}`)
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

  // ponytail: warn on accidental page close/refresh once the study has started (skip in dev mode)
  useEffect(() => {
    if (!idGiven || import.meta.env.VITE_DEV_MODE === 'true') return
    const handler = (e) => { e.preventDefault(); e.returnValue = '' }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [idGiven])

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
          {conditionHasChat(condition) && <ChatView
            task={tasks[ctxStore.state.taskIndex] || tasks[ctxStore.state.taskIndex - 1]}
          />}
        </div>
      </>
      }
    </>
  )
}

export default App
