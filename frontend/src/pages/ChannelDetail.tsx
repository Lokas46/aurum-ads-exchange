import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchChannel, Channel, createOrder } from '../api/client'
import { hapticFeedback, showConfirm } from '../api/telegram'
import { useUser } from '../context/UserContext'
import UserHeader from '../components/UserHeader'

export default function ChannelDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { balance, refreshBalance } = useUser()
  const [channel, setChannel] = useState<Channel | null>(null)
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    if (id) fetchChannel(Number(id)).then(setChannel).catch(() => {})
  }, [id])

  async function handleOrder() {
    if (!channel) return
    if (balance < (channel.price_per_post ?? 0)) {
      window.Telegram?.WebApp?.showAlert('Недостаточно средств. Пополни кошелёк.')
      return
    }
    const ok = await showConfirm(`Заказать пост в «${channel.title}» за ${channel.price_per_post} ₽?`)
    if (!ok) return
    setAdding(true)
    try {
      await createOrder(channel.id, '')
      hapticFeedback('medium')
      await refreshBalance()
      window.Telegram?.WebApp?.showAlert('✅ Заказ создан! Ожидай подтверждения от владельца.')
      navigate('/miniapp/orders')
    } catch (e: any) {
      window.Telegram?.WebApp?.showAlert(`❌ Ошибка: ${e.message}`)
    }
    setAdding(false)
  }

  if (!channel) {
    return <div className="page"><div className="loading">Загрузка</div></div>
  }

  const canOrder = balance >= (channel.price_per_post ?? 0)

  return (
    <div className="page">
      <UserHeader />
      <div className="detail-header">
        <button className="back-btn" onClick={() => navigate('/miniapp')}>← Назад</button>
        <h1>{channel.title}</h1>
        {channel.is_verified && (
          <span className="verified-badge" style={{ marginTop: 6, display: 'inline-block' }}>✓ Верифицирован</span>
        )}
      </div>

      <div className="stat-grid">
        <div className="stat-item">
          <div className="value">{channel.subscribers_count?.toLocaleString() ?? '—'}</div>
          <div className="label">Подписчиков</div>
        </div>
        <div className="stat-item">
          <div className="value" style={{ color: '#34d399' }}>{channel.price_per_post ?? '—'} ₽</div>
          <div className="label">Цена за пост</div>
        </div>
      </div>

      {channel.description && (
        <div className="glass-card" style={{ marginBottom: 16, lineHeight: 1.6, fontSize: 14, color: '#a0a0c0' }}>
          {channel.description}
        </div>
      )}

      {channel.categories && (
        <div className="glass-card" style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Категории
          </div>
          <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
            {(channel.categories as string).split(',').map((c: string, i: number) => (
              <span key={i} className="category-tag" style={{
                background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.2)',
                color: '#818cf8', fontSize: 11, padding: '2px 8px', borderRadius: 6
              }}>{c.trim()}</span>
            ))}
          </div>
        </div>
      )}

      <div className="glass-card" style={{ marginBottom: 16, fontSize: 13, color: '#6b7280' }}>
        Твой баланс: <span style={{ color: '#34d399', fontWeight: 600 }}>{balance.toFixed(2)} ₽</span>
        {!canOrder && <span style={{ display: 'block', marginTop: 4, color: '#f87171', fontSize: 12 }}>
          ⚠️ Недостаточно средств. Пополни кошелёк
        </span>}
      </div>

      <div className="actions">
        <button className="glass-btn" onClick={handleOrder} disabled={adding || !canOrder}
          style={{ opacity: adding || !canOrder ? 0.5 : 1, width: '100%' }}>
          {adding ? 'Оформляем...' : '📝 Заказать рекламу'}
        </button>
        {channel.username && (
          <a href={`https://t.me/${channel.username}`} target="_blank" rel="noopener noreferrer"
            className="glass-btn-secondary" style={{ textAlign: 'center', width: '100%' }}>
            🔗 Открыть канал
          </a>
        )}
      </div>
    </div>
  )
}
