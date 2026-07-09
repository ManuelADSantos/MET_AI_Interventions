import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import ConsentPage from './components/ConsentPage.jsx'
import SyncPage from './components/SyncPage.jsx'
import { StateProvider } from './scripts/store.jsx'
import { NextUIProvider } from '@nextui-org/react'
import loadTasks from './scripts/taskParser/taskParser'
import 'bootstrap-icons/font/bootstrap-icons.css'
import './index.css'

/** Condition setup — plug and play:
 * drop `<name>_tasks.md` (+ optional `study_info/<name>_studyinfo.md`) into
 * customizations/tasks/ and the condition "<name>" exists (underscores in the
 * filename become hyphens in the condition, e.g. no_ai -> no-ai). No code changes.
 */
const taskFiles = import.meta.glob('/public/*_tasks.md', { query: '?raw', import: 'default', eager: true })
const infoFiles = import.meta.glob('/public/study_info/*_studyinfo.md', { query: '?raw', import: 'default', eager: true })

const randomize = import.meta.env.VITE_RANDOMIZE_TASKS !== 'false'
const opts = { randomize }

const tasksPerCondition = Object.fromEntries(Object.entries(taskFiles).map(([path, raw]) => {
  const name = path.slice('/public/'.length, -'_tasks.md'.length)
  const info = loadTasks(infoFiles[`/public/study_info/${name}_studyinfo.md`] || '', opts) || []
  const tasks = loadTasks(raw, opts) || []
  return [name.replace(/_/g, '-'), [...info, ...tasks.map((p) => ({ ...p, sourceIndex: p.sourceIndex + info.length }))]]
}))

const urlParams = new URLSearchParams(window.location.search)
// ponytail: URL ?condition=no_ai overrides config; normalize underscore to hyphen
const urlCondition = urlParams.get('condition')?.replace('_', '-')
const condition = urlCondition || import.meta.env.VITE_PCTP_CONDITION || 'no-ai'

// Strip Prolific params from the address bar so participants can't read or tweak them
// mid-study (App.jsx captured them at import time, before this line runs)
if (window.location.search) window.history.replaceState(null, '', window.location.pathname)

const useAutoProctor = import.meta.env.VITE_USE_AUTOPROCTOR === 'true'
const isIframe = window.self !== window.top

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
