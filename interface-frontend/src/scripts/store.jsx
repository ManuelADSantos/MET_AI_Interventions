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
  chatUsedOnPage: false,
  reliabilityWarningVisible: false
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
      case 'SHOW_RELIABILITY_WARNING':
        return {...state, reliabilityWarningVisible: true}
      case 'NEXT_TASK':
        return {...state, taskIndex: state.taskIndex + 1, chatEnabled: !!action.payload?.chatEnabled, chatUsedOnPage: false, reliabilityWarningVisible: false, taskChatDraft: null}
      case 'SET_TASK_INDEX':
        return {...state, taskIndex: action.payload.index, chatEnabled: !!action.payload.chatEnabled, chatUsedOnPage: false, reliabilityWarningVisible: false, taskChatDraft: null}
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
          responses: action.payload.responses
        }
        return {...state, tasks: {...state.tasks, [action.payload.index]: updatedRes}}
      case 'UPDATE_TASK_TIMESTAMP':
        const resToStamp = state.tasks[action.payload.index] || {ts: undefined, responses: {}}
        const stampedRes = {...resToStamp, ts: action.payload.ts}
        return {...state, tasks: {...state.tasks, [action.payload.index]: stampedRes}}
      case 'LOG_RELIABILITY_CARD_EVENT': {
        const event = action.payload
        const isPresented = event.type === 'reliability_card_presented'
        if (isPresented && state.interactionLog.some((item) =>
          item.type === 'reliability_card_presented' && item.taskId === event.taskId
        )) return state

        if (!isPresented) {
          return {...state, interactionLog: [...state.interactionLog, event]}
        }

        const task = state.tasks[event.taskId] || {ts: undefined, responses: {}}
        return {
          ...state,
          interactionLog: [...state.interactionLog, event],
          tasks: {
            ...state.tasks,
            [event.taskId]: {...task, reliabilityShownAt: event.timestamp}
          }
        }
      }
      case 'UPDATE_MESSAGES':
        const updatedMessages = [...state.messages, action.payload.prompt, action.payload.response]
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
