import { useMemo, useState } from 'react'
import './App.css'
import CounterPick from './pages/CounterPick'
import TierList from './pages/TierList'
import Quiz from './pages/Quiz'
import Challenge from './pages/Challenge'
import PatchExplainer from './pages/PatchExplainer'
import { API_BASE } from './api'

type Tab = 'counter' | 'tier' | 'quiz' | 'daily' | 'patch'

function App() {
  const [tab, setTab] = useState<Tab>('counter')
  const tabs: { key: Tab; label: string }[] = useMemo(() => ([
    { key: 'counter', label: 'Counter‑Pick' },
    { key: 'tier', label: 'Tier List' },
    { key: 'quiz', label: 'Quiz' },
    { key: 'daily', label: 'Daily' },
    { key: 'patch', label: 'Patch Explainer' },
  ]), [])

  return (
    <div className="container">
      <header className="header">
        <h1>MLBB Mini App</h1>
        <small className="api">API: {API_BASE}</small>
      </header>

      <nav className="tabs">
        {tabs.map(t => (
          <button
            key={t.key}
            className={tab === t.key ? 'tab active' : 'tab'}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="content">
        {tab === 'counter' && <CounterPick />}
        {tab === 'tier' && <TierList />}
        {tab === 'quiz' && <Quiz />}
        {tab === 'daily' && <Challenge />}
        {tab === 'patch' && <PatchExplainer />}
      </main>
    </div>
  )
}

export default App
