import { createContext, useReducer } from 'react'

const init = {
  participantId: '',
  taskIndex: -1,
  messages: [],
  interactionLog: [],
  taskChatDraft: null,
  tasks: {},
  condition: undefined,
  chatEnabled: false,
  displayChatOnboarding: true,
  chatUsedOnPage: false
}

const store = createContext(init)
const { Provider } = store

const StateProvider = ({ children }) => {
  const [state, dispatch] = useReducer((state, action) => {
    switch (action.type) {
      case 'UPDATE_ID':
        return {...state, participantId: action.payload.id}
      case 'UPDATE_CONDITION':
        return {...state, condition: action.payload.condition}
      case 'DISMISS_ONBOARDING':
          return {...state, displayChatOnboarding: false}
      case 'TOGGLE_CHAT_USED':
        return {...state, chatUsedOnPage: action.payload.value}
      // Interstitial reflection hides the chat AND its transcript — the explain-back is
      // worthless if the participant can scroll back and copy. Restored on the next page.
      case 'SET_CHAT_ENABLED':
        return {...state, chatEnabled: action.payload.value}
      case 'NEXT_TASK':
        return {...state, taskIndex: state.taskIndex + 1, chatEnabled: !!action.payload?.chatEnabled, chatUsedOnPage: false, taskChatDraft: null}
      case 'SET_TASK_INDEX':
        return {...state, taskIndex: action.payload.index, chatEnabled: !!action.payload.chatEnabled, chatUsedOnPage: false, taskChatDraft: null}
      case 'TASK_ADDED_TO_CHAT':
        return {
          ...state,
          taskChatDraft: { taskId: action.payload.taskId, insertedText: action.payload.insertedText, editedBeforeSend: false },
          interactionLog: [...state.interactionLog, {
            type: 'task_added_to_chat',
            taskId: action.payload.taskId,
            timestamp: action.payload.timestamp,
            draftWasSent: false,
            editedBeforeSend: false
          }]
        }
      case 'TASK_CHAT_DRAFT_EDITED': {
        if (!state.taskChatDraft || state.taskChatDraft.taskId !== action.payload.taskId || state.taskChatDraft.editedBeforeSend) return state
        const interactionLog = [...state.interactionLog]
        for (let i = interactionLog.length - 1; i >= 0; i -= 1) {
          const event = interactionLog[i]
          if (event.type === 'task_added_to_chat' && event.taskId === action.payload.taskId && !event.draftWasSent) {
            interactionLog[i] = {...event, editedBeforeSend: true}
            break
          }
        }
        return {...state, interactionLog, taskChatDraft: {...state.taskChatDraft, editedBeforeSend: true}}
      }
      case 'TASK_CHAT_DRAFT_SENT': {
        const interactionLog = [...state.interactionLog]
        for (let i = interactionLog.length - 1; i >= 0; i -= 1) {
          const event = interactionLog[i]
          if (event.type === 'task_added_to_chat' && event.taskId === action.payload.taskId && !event.draftWasSent) {
            interactionLog[i] = {
              ...event,
              draftWasSent: true,
              editedBeforeSend: event.editedBeforeSend || action.payload.editedBeforeSend,
              sentTimestamp: action.payload.timestamp
            }
            break
          }
        }
        return {...state, interactionLog, taskChatDraft: null}
      }
      case 'UPDATE_RESPONSES':
        const resToUpdate = state.tasks[action.payload.index] || {ts: undefined, responses: {}}
        const updatedRes = {
          ...resToUpdate,
          displayIndex: state.taskIndex,
          ...(action.payload.title ? {title: action.payload.title} : {}),
          responses: action.payload.responses
        }
        return {...state, tasks: {...state.tasks, [action.payload.index]: updatedRes}}
      case 'UPDATE_TASK_TIMESTAMP':
        const resToStamp = state.tasks[action.payload.index] || {ts: undefined, responses: {}}
        const stampedRes = {...resToStamp, ts: action.payload.ts}
        return {...state, tasks: {...state.tasks, [action.payload.index]: stampedRes}}
      case 'LOG_INTERACTION':
        return {...state, interactionLog: [...state.interactionLog, action.payload]}
      case 'UPDATE_MESSAGES':
        // ponytail: dual-column alternatives appends response_b as a third entry
        const updatedMessages = [...state.messages, action.payload.prompt, action.payload.response]
        if (action.payload.response_b) updatedMessages.push(action.payload.response_b)
        return {...state, messages: updatedMessages}
      case 'ALL_DONE':
        return {...state, chatEnabled: false}
      default:
        throw new TypeError(`Error: Invalid action type ${action.type}`)
    }
  }, init)

  return <Provider value={{state, dispatch}}>{children}</Provider>
}

export {store, StateProvider}
