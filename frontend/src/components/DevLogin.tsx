import { useEffect, useRef, useState } from 'react'
import { apiFetch, UserProfile } from '../api/client'

const BOT_USERNAME = 'aurumads_bot'
const ADMIN_IDS = [1836926514, 37175, 34175]

declare global {
  interface Window {
    onTelegramAuth?: (user: any) => void
  }
}

function isTgWebApp(): boolean {
  return !!(window.Telegram?.WebApp?.initData)
}

export default function DevLogin() {
  const [idInput, setIdInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const widgetRef = useRef<HTMLDivElement>(null)
  const scriptLoaded = useRef(false)

  const inTg = isTgWebApp()

  useEffect(() => {
    if (inTg || scriptLoaded.current) return
    scriptLoaded.current = true

    window.onTelegramAuth = async (user: any) => {
      setLoading(true)
      setError('')
      try {
        const prof = await apiFetch<UserProfile>('/api/auth/tg-login', {
          method: 'POST',
          body: JSON.stringify({
            id: user.id,
            first_name: user.first_name || '',
            last_name: user.last_name || '',
            username: user.username || '',
            photo_url: user.photo_url || '',
            auth_date: user.auth_date || 0,
            hash: user.hash || '',
          }),
        })
        sessionStorage.setItem('dev_user_id', String(prof.id))
        window.location.reload()
      } catch (e: any) {
        setError('Ошибка входа: ' + (e?.message || 'неизвестная'))
        setLoading(false)
      }
    }

    const s = document.createElement('script')
    s.src = 'https://telegram.org/js/telegram-widget.js?22'
    s.setAttribute('data-telegram-login', BOT_USERNAME)
    s.setAttribute('data-size', 'large')
    s.setAttribute('data-radius', '12')
    s.setAttribute('data-onauth', 'onTelegramAuth(user)')
    s.setAttribute('data-request-access', 'write')
    s.async = true
    widgetRef.current?.appendChild(s)

    return () => { window.onTelegramAuth = undefined }
  }, [inTg])

  async function handleDevLogin(id: number) {
    setLoading(true)
    setError('')
    try {
      await apiFetch<UserProfile>('/api/auth/dev-login?user_id=' + id)
      sessionStorage.setItem('dev_user_id', String(id))
      window.location.reload()
    } catch (e: any) {
      setError('Ошибка: ' + (e?.message || 'неизвестная'))
      setLoading(false)
    }
  }

  return (
    <div className="page" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: 20 }}>
      <div style={{ fontSize: 28, fontWeight: 700, color: '#f0f0ff', marginBottom: 8 }}>Aurum Ads</div>
      <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 24 }}>Telegram Ad Exchange</div>

      {!inTg && (
        <div id="telegram-login-widget" ref={widgetRef} style={{ marginBottom: 24, display: 'flex', justifyContent: 'center' }}></div>
      )}

      <div style={{ width: '100%', maxWidth: 320, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.1)' }} />
        <div style={{ fontSize: 11, color: '#6b7280', textTransform: 'uppercase' }}>вход</div>
        <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.1)' }} />
      </div>

      {error && (
        <div style={{ fontSize: 12, color: '#f87171', marginBottom: 12, wordBreak: 'break-all', maxWidth: 320, textAlign: 'center' }}>
          {error}
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, width: '100%', maxWidth: 320 }}>
        {ADMIN_IDS.map(id => (
          <button key={id} className="glass-btn" style={{ width: '100%', padding: '10px 0', fontSize: 13, opacity: loading ? 0.6 : 1 }}
            onClick={() => handleDevLogin(id)} disabled={loading}>
            {loading ? '⏳' : `Войти как админ #${id}`}
          </button>
        ))}
        <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
          <input type="number" placeholder="Telegram ID" value={idInput}
            onChange={e => setIdInput(e.target.value)}
            style={{ flex: 1, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 10, padding: '10px 14px', color: '#e0e0e0', fontSize: 13, outline: 'none' }}
          />
          <button className="glass-btn" style={{ padding: '10px 20px', fontSize: 13, opacity: idInput && !loading ? 1 : 0.5 }}
            disabled={!idInput || loading} onClick={() => handleDevLogin(Number(idInput))}>
            Ok
          </button>
        </div>
      </div>
    </div>
  )
}