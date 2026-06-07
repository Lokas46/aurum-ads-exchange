import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { myChannels, Channel } from '../api/client'
import UserHeader from '../components/UserHeader'

export default function MyChannels() {
  const navigate = useNavigate()
  const [channels, setChannels] = useState<Channel[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    myChannels()
      .then(data => { setChannels(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <UserHeader />
      <div className="header" style={{ padding: '0 0 12px 0' }}>
        <h1>Мои каналы</h1>
        <p>Зарабатывай на рекламе</p>
      </div>

      <div className="glass-btn" style={{ width: '100%', marginBottom: 16, cursor: 'pointer' }}
        onClick={() => navigate('/miniapp/add-channel')}>
        ➕ Добавить канал
      </div>

      {loading ? <div className="loading">Загрузка</div> : channels.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📡</div>
          <h3>Нет каналов</h3>
          <p>Нажми «Добавить канал», чтобы зарегистрировать канал</p>
        </div>
      ) : (
        channels.map(ch => (
          <div key={ch.id} className="glass-card" style={{ marginBottom: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, color: '#f0f0ff' }}>{ch.title}</div>
                <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>
                  👥 {ch.subscribers_count?.toLocaleString() ?? '—'}  ·  {ch.price_per_post ?? '—'} ₽
                </div>
              </div>
              <div style={{
                fontSize: 11, padding: '3px 10px', borderRadius: 6, fontWeight: 600,
                background: ch.is_active ? 'rgba(52,211,153,0.15)' : ch.is_moderated ? 'rgba(248,113,113,0.15)' : 'rgba(251,191,36,0.15)',
                color: ch.is_active ? '#34d399' : ch.is_moderated ? '#f87171' : '#fbbf24',
                border: `1px solid ${ch.is_active ? 'rgba(52,211,153,0.2)' : ch.is_moderated ? 'rgba(248,113,113,0.2)' : 'rgba(251,191,36,0.2)'}`,
              }}>
                {ch.is_active ? 'Активен' : ch.is_moderated ? 'Отклонён' : 'На модерации'}
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  )
}
