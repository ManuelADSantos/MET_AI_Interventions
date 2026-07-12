import loadTasks from './taskParser/taskParser'

// ponytail: auto-discover conditions from *_tasks.md files — drop a new file and the condition exists
const taskFiles = import.meta.glob('/public/*_tasks.md', { query: '?raw', import: 'default', eager: true })
const infoFiles = import.meta.glob('/public/study_info/*_studyinfo.md', { query: '?raw', import: 'default', eager: true })

const randomize = import.meta.env.VITE_RANDOMIZE_TASKS !== 'false'
const opts = { randomize }

export const tasksPerCondition = Object.fromEntries(Object.entries(taskFiles).map(([path, raw]) => {
  const name = path.slice('/public/'.length, -'_tasks.md'.length)
  const info = loadTasks(infoFiles[`/public/study_info/${name}_studyinfo.md`] || '', opts) || []
  const tasks = loadTasks(raw, opts) || []
  return [name.replace(/_/g, '-'), [...info, ...tasks.map((p) => ({ ...p, sourceIndex: p.sourceIndex + info.length }))]]
}))

// ponytail: condition has chat unless it starts with "no-"
export const conditionHasChat = (condition) => !condition?.startsWith('no-')
