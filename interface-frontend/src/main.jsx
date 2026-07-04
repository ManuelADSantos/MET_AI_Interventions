import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { StateProvider } from './scripts/store.jsx'
import { NextUIProvider } from '@nextui-org/react'
import loadTasks from './scripts/taskParser/taskParser'
import 'bootstrap-icons/font/bootstrap-icons.css'
import './index.css'

/** Condition setup
 * 1. Load info documents & surveys from the public/ directory
 * 2. Run taskParser to convert these to JSON
 * 3. Use .env configuration to determine which condition to show
 */
import aiTaskFile from '/public/ai_tasks.md?raw'
import aiStudyInfoFile from '/public/examples/ai_studyinfo_example.md?raw'
import noAiTaskFile from '/public/no-ai_tasks.md?raw'
import noAiStudyInfoFile from '/public/examples/no-ai_studyinfo_example.md?raw'

const randomize = import.meta.env.VITE_RANDOMIZE_TASKS !== 'false'
const opts = { randomize }
const aiTasks = loadTasks(aiTaskFile, opts)
const aiStudyInfo = loadTasks(aiStudyInfoFile, opts)
const noAiTasks = loadTasks(noAiTaskFile, opts)
const noAiStudyInfo = loadTasks(noAiStudyInfoFile, opts)

const condition = import.meta.env.VITE_PCTP_CONDITION || 'no-ai'

const tasksPerCondition = {
  'ai': [...aiStudyInfo, ...aiTasks.map((p) => {return { ...p, sourceIndex: p.sourceIndex + aiStudyInfo.length }})],
  'no-ai': [...noAiStudyInfo, ...noAiTasks.map((p) => {return { ...p, sourceIndex: p.sourceIndex + aiStudyInfo.length }})]
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <StateProvider>
    <NextUIProvider>
      <App condition={condition} tasks={tasksPerCondition[condition]} />
    </NextUIProvider>
  </StateProvider>
)
