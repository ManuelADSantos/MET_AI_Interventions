import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import ConsentPage from './components/ConsentPage.jsx'
import SyncPage from './components/SyncPage.jsx'
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
import aiStudyInfoFile from '/public/study_info/ai_studyinfo.md?raw'
import noAiTaskFile from '/public/no_ai_tasks.md?raw'
import noAiStudyInfoFile from '/public/study_info/no_ai_studyinfo.md?raw'

const randomize = import.meta.env.VITE_RANDOMIZE_TASKS !== 'false'
const opts = { randomize }
const aiTasks = loadTasks(aiTaskFile, opts)
const aiStudyInfo = loadTasks(aiStudyInfoFile, opts)
const noAiTasks = loadTasks(noAiTaskFile, opts)
const noAiStudyInfo = loadTasks(noAiStudyInfoFile, opts)

const urlParams = new URLSearchParams(window.location.search)
// ponytail: URL ?condition=no_ai overrides config; normalize underscore to hyphen
const urlCondition = urlParams.get('condition')?.replace('_', '-')
const condition = urlCondition || import.meta.env.VITE_PCTP_CONDITION || 'no-ai'

const useAutoProctor = import.meta.env.VITE_USE_AUTOPROCTOR === 'true'
const isIframe = window.self !== window.top

const tasksPerCondition = {
  'ai': [...aiStudyInfo, ...aiTasks.map((p) => {return { ...p, sourceIndex: p.sourceIndex + aiStudyInfo.length }})],
  'no-ai': [...noAiStudyInfo, ...noAiTasks.map((p) => {return { ...p, sourceIndex: p.sourceIndex + aiStudyInfo.length }})]
}

function Main() {
  // Inside AutoProctor iframe → SyncPage login
  if (isIframe && useAutoProctor) return <SyncPage />

  // Prolific arrival with AutoProctor → consent flow
  if (useAutoProctor && urlParams.get('PROLIFIC_PID')) {
    return (
      <ConsentPage
        prolificPid={urlParams.get('PROLIFIC_PID')}
        prolificStudyId={urlParams.get('STUDY_ID')}
        prolificSessionId={urlParams.get('SESSION_ID')}
        condition={condition}
      />
    )
  }

  // Normal flow (no AutoProctor or dev mode)
  return <App condition={condition} tasks={tasksPerCondition[condition]} />
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <StateProvider>
    <NextUIProvider>
      <Main />
    </NextUIProvider>
  </StateProvider>
)
