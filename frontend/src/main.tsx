import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { initTelegram, verifyInitData } from './tg'

// Init Telegram Mini App integration (safe in browser too)
initTelegram()
verifyInitData().catch(err => console.warn('[TG verify]', err))

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
