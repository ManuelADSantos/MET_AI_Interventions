import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import ConsentPage from './components/ConsentPage.jsx'
import SyncPage from './components/SyncPage.jsx'
import { StateProvider } from './scripts/store.jsx'
import { NextUIProvider } from '@nextui-org/react'
import { tasksPerCondition } from './scripts/conditions'
import 'bootstrap-icons/font/bootstrap-icons.css'
import './index.css'

const urlParams = new URLSearchParams(window.location.search)
// ponytail: condition comes from URL only — ?condition=ai or ?condition=no_ai
const condition = urlParams.get('condition')?.replace('_', '-') || 'ai'

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
