import { useContext, useState } from "react"
import { store } from "./scripts/store"
import { checkParticipation } from "./scripts/dbService"
import TaskView from './components/tasks/TaskView'
import ChatView from "./components/chat/ChatView"
import { Button, Card, CardBody, Input, CardHeader } from '@nextui-org/react'

const App = ({ condition, tasks }) => {
  const [idGiven, setIdGiven] = useState(false)
  const [idError, setIdError] = useState('')
  const ctxStore = useContext(store)

  const handleIdSubmit = async (e) => {
    e.preventDefault()

    /* Don't require ID if configured in .env */
    if (import.meta.env.VITE_DEV_MODE === 'true') {
      ctxStore.dispatch({type: 'UPDATE_ID', payload: {id: e.target[0].value}})
      ctxStore.dispatch({type: 'UPDATE_CONDITION', payload: {condition: condition}})
      ctxStore.dispatch({type: 'NEXT_TASK'})
      setIdGiven(true)
      return
    }

    /* ID should be pretty long to discourage participants from submitting whatever / partial IDs  */
    if (e.target[0].value.trim().length < 16) {
      setIdGiven(false)
      setIdError('Please enter your Prolific ID.')
      return
    }

    /* Check whether the ID has already been registered in the database */
    const res = await checkParticipation(e.target[0].value)

    /* If there's no errors, allow proceeding */
    if (!res.error) {
      ctxStore.dispatch({type: 'UPDATE_ID', payload: {id: e.target[0].value}})
      ctxStore.dispatch({type: 'UPDATE_CONDITION', payload: {condition: condition}})
      ctxStore.dispatch({type: 'NEXT_TASK'})
      setIdGiven(true)
    } else {
      setIdGiven(false)
      setIdError(res.error)
    }
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
          <ChatView sourceIndex={
            tasks[ctxStore.state.taskIndex] 
            ? tasks[ctxStore.state.taskIndex].sourceIndex 
            : tasks[ctxStore.state.taskIndex - 1].sourceIndex
          } />
        </div>
      </>
      }
    </>
  )
}

export default App
