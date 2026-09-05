import { useEffect, useMemo, useState } from 'react'
import './App.css'

type Task = {
  task_id: string
  goal_text: string
  status: string
  created_at?: string
  updated_at?: string
  metadata?: Record<string, unknown>
  status_message?: string | null
  steps?: Array<{ id: string; description: string; status: string; step_index: number }>
}

type ChatEntry = {
  role: 'user' | 'assistant'
  text: string
  time: string
}

type HealthResponse = {
  status?: string
  environment?: string
  database?: { status?: string; backend?: string }
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const formatTime = (value?: string) => {
  if (!value) return 'now'
  try {
    return new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return 'now'
  }
}

const getStatusTone = (status: string) => {
  const normalized = (status || '').toLowerCase()
  if (normalized === 'completed' || normalized === 'done') return 'done'
  if (normalized === 'running') return 'running'
  if (normalized === 'planned' || normalized === 'pending' || normalized === 'queued') return 'queued'
  return 'queued'
}

const buildAssistantReply = (task: Task) => {
  const pendingStep = task.steps?.find((step) => step.status === 'pending')

  if (task.status === 'completed') {
    return `Task finished successfully. I completed the workflow and saved the result.`
  }

  if (task.status === 'running') {
    return pendingStep
      ? `Task is active. Current step: ${pendingStep.description}`
      : 'Task is active and processing the next step.'
  }

  if (task.status === 'planned') {
    return `Task accepted and planned. ${task.steps?.length ?? 0} steps are queued for execution.`
  }

  return 'Task is queued and waiting to start.'
}

function App() {
  const [prompt, setPrompt] = useState('')
  const [tasks, setTasks] = useState<Task[]>([])
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('Type a task and the agent will plan and execute it.')
  const [chat, setChat] = useState<ChatEntry[]>([])

  const refreshData = async () => {
    try {
      const [taskResponse, healthResponse] = await Promise.all([
        fetch(`${API_BASE}/tasks`),
        fetch(`${API_BASE}/health`),
      ])

      if (!taskResponse.ok) throw new Error('Unable to load task list from backend.')
      const taskPayload = await taskResponse.json()
      const healthPayload = healthResponse.ok ? await healthResponse.json() : { status: 'offline' }

      setTasks(taskPayload.tasks || [])
      setHealth(healthPayload)

      const latestTask = (taskPayload.tasks || [])[0]
      if (latestTask) {
        setChat([
          {
            role: 'user',
            text: latestTask.goal_text,
            time: formatTime(latestTask.created_at),
          },
          {
            role: 'assistant',
            text: buildAssistantReply(latestTask),
            time: formatTime(latestTask.updated_at || latestTask.created_at),
          },
        ])
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Backend is not responding.')
    }
  }

  useEffect(() => {
    void refreshData()
  }, [])

  const queuedCount = useMemo(
    () => tasks.filter((task) => ['pending', 'planned', 'running'].includes(task.status)).length,
    [tasks],
  )

  const completedCount = useMemo(
    () => tasks.filter((task) => task.status === 'completed').length,
    [tasks],
  )

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const trimmed = prompt.trim()
    if (!trimmed) {
      setMessage('Please type a task before sending.')
      return
    }

    setLoading(true)
    setMessage('Sending task to the agent...')

    try {
      const createResponse = await fetch(`${API_BASE}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          goal_text: trimmed,
          metadata: {
            source: 'dashboard',
            model: 'Google Gemini',
          },
        }),
      })

      if (!createResponse.ok) throw new Error('Task creation failed.')
      const createdTask = await createResponse.json()

      const executeResponse = await fetch(`${API_BASE}/tasks/${createdTask.task_id}/execute`, {
        method: 'POST',
      })

      if (!executeResponse.ok) {
        throw new Error('Task was created but execution failed.')
      }

      const executionPayload = await executeResponse.json()
      const assistantText = executionPayload?.execution?.result?.result?.results?.length
        ? executionPayload.execution.result.result.results.join(' ')
        : buildAssistantReply(createdTask)

      setChat((current) => [
        ...current,
        { role: 'user', text: trimmed, time: 'now' },
        { role: 'assistant', text: assistantText, time: 'now' },
      ])

      setPrompt('')
      setMessage('Task sent successfully.')
      await refreshData()
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not send the task.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand-mark">S</div>
          <div>
            <p className="eyebrow">system</p>
            <h2>SLMAS</h2>
          </div>
        </div>

        <nav className="nav-list">
          <button type="button" className="nav-item active">Overview</button>
          <button type="button" className="nav-item">Tasks</button>
          <button type="button" className="nav-item">Chat</button>
        </nav>

        <div className="status-box">
          <p className="eyebrow small">status</p>
          <strong>{health?.database?.status === 'healthy' ? 'Healthy' : 'Checking'}</strong>
          <span>{health?.database?.backend || 'sqlite'} database</span>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <p className="eyebrow small">live operations</p>
            <h1>Ask the agent</h1>
          </div>
          <div className="topbar-actions">
            <button type="button" className="secondary-button" onClick={() => void refreshData()}>
              Refresh
            </button>
          </div>
        </header>

        <div className="info-banner">{message}</div>

        <section className="stats-grid">
          <article className="mini-card">
            <span>Queue</span>
            <strong>{queuedCount}</strong>
          </article>
          <article className="mini-card">
            <span>Completed</span>
            <strong>{completedCount}</strong>
          </article>
          <article className="mini-card">
            <span>System</span>
            <strong>{health?.status === 'ok' ? 'Online' : 'Idle'}</strong>
          </article>
        </section>

        <section className="chat-panel">
          <div className="panel-header">
            <h3>Chat with AI</h3>
            <span>Simple view</span>
          </div>

          <form onSubmit={handleSubmit} className="composer">
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Type your task here... e.g. Summarize sales data and create a brief"
              rows={4}
            />
            <div className="composer-actions">
              <button type="submit" className="primary-button" disabled={loading}>
                {loading ? 'Sending...' : 'Send task'}
              </button>
            </div>
          </form>

          <div className="conversation">
            {chat.length ? (
              chat.map((entry, index) => (
                <div key={`${entry.role}-${index}-${entry.time}`} className={`bubble ${entry.role}`}>
                  <div className="bubble-header">
                    <span>{entry.role === 'user' ? 'You' : 'AI'}</span>
                    <small>{entry.time}</small>
                  </div>
                  <p>{entry.text}</p>
                </div>
              ))
            ) : (
              <div className="empty-state">No chat history yet. Type your first task to begin.</div>
            )}
          </div>
        </section>

        <section className="board-grid">
          <article className="panel">
            <div className="panel-header">
              <h3>Queued tasks</h3>
              <span>latest</span>
            </div>

            <div className="task-list">
              {tasks.length ? (
                tasks.slice(0, 6).map((task) => (
                  <div key={task.task_id} className="task-row">
                    <div>
                      <strong>{task.goal_text}</strong>
                      <small>{formatTime(task.created_at)}</small>
                    </div>
                    <span className={`status-pill ${getStatusTone(task.status)}`}>{task.status}</span>
                  </div>
                ))
              ) : (
                <div className="empty-state">No tasks in queue yet.</div>
              )}
            </div>
          </article>

          <article className="panel">
            <div className="panel-header">
              <h3>Agent summary</h3>
              <span>status</span>
            </div>

            <div className="summary-box">
              <div>
                <label>Last task</label>
                <strong>{tasks[0]?.goal_text || 'No task yet'}</strong>
              </div>
              <div>
                <label>Result</label>
                <strong>{tasks[0]?.status || 'waiting'}</strong>
              </div>
            </div>
          </article>
        </section>
      </main>
    </div>
  )
}

export default App
