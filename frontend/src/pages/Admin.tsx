import { useEffect, useState } from 'react'
import { useUser } from '../context/UserContext'
import { apiFetch } from '../api/client'
import UserHeader from '../components/UserHeader'

interface ModChannel {
  id: number; title: string; username: string | null
  description: string | null; price_per_post: number | null
  categories: string | null; owner_id: number
  is_moderated: boolean; is_active: boolean
  subscribers_count: number | null; bot_added: boolean | null
  created_at?: string
}

interface WithdrawReq {
  id: number; user_id: number; amount: number
  fee: number; net_amount: number; status: string
  created_at: string
}

interface Dashboard {
  users: number; channels: number; orders: number
  pending_channels: number; active_channels: number
  pending_orders: number; active_orders: number
}

type Tab = 'dashboard' | 'moderation' | 'channels' | 'withdrawals' | 'crypto'

export default function Admin() {
  const { profile, balance } = useUser()
  const [tab, setTab] = useState<Tab>('dashboard')
  const [msg, setMsg] = useState('')
  const [dash, setDash] = useState<Dashboard | null>(null)
  const [pending, setPending] = useState<ModChannel[]>([])
  const [allChannels, setAllChannels] = useState<ModChannel[]>([])
  const [withdrawals, setWithdrawals] = useState<WithdrawReq[]>([])
  const [cryptoBalance, setCryptoBalance] = useState<number | null>(null)
  const [webhookStatus, setWebhookStatus] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!profile?.is_admin) return
    loadData()
  }, [profile])

  function loadData() {
    setLoading(true)
    Promise.all([
      apiFetch<Dashboard>('/api/admin/dashboard').then(setDash).catch(() => {}),
      apiFetch<ModChannel[]>('/api/channels/all').then(data => {
        setAllChannels(data)
        setPending(data.filter(ch => !ch.is_moderated))
      }).catch(() => {}),
      apiFetch<WithdrawReq[]>('/api/admin/withdraw-requests').then(setWithdrawals).catch(() => {}),
      apiFetch<{ balance: any }>('/api/admin/cryptobot-balance')
        .then(d => setCryptoBalance(d.balance?.[0]?.available ?? 0)).catch(() => {}),
    ]).finally(() => setLoading(false))
  }

  async function moderate(id: number, approve: boolean) {
    setMsg('')
    try {
      await apiFetch(`/api/channels/${id}/moderate`, {
        method: 'POST',
        body: JSON.stringify({ approve }),
      })
      setMsg(approve ? `✅ Канал #${id} одобрен` : `❌ Канал #${id} отклонён`)
      const data = await apiFetch<ModChannel[]>('/api/channels/all')
      setAllChannels(data)
      setPending(data.filter(ch => !ch.is_moderated))
    } catch (e: any) { setMsg(e?.message || 'Ошибка') }
  }

  async function setupWebhook() {
    setWebhookStatus('⏳...')
    try {
      const d = await apiFetch<{ webhook_url: string }>('/api/admin/cryptobot-setup')
      setWebhookStatus('✅ URL: ' + d.webhook_url + '. Настрой вручную в @CryptoBot.')
    } catch { setWebhookStatus('❌ Ошибка сети') }
  }

  if (!profile?.is_admin) {
    return (
      <div className="page">
        <UserHeader />
        <div className="empty-state">
          <div className="empty-icon">🔒</div>
          <h3>Доступ запрещён</h3>
          <p>Только администраторы могут просматривать эту страницу.</p>
        </div>
      </div>
    )
  }

  const tabs: { key: Tab; label: string; icon: string; badge?: string | number }[] = [
    { key: 'dashboard', label: 'Дашборд', icon: '📊' },
    { key: 'moderation', label: 'Модерация', icon: '🛡️', badge: pending.length || undefined },
    { key: 'channels', label: 'Каналы', icon: '📢' },
    { key: 'withdrawals', label: 'Выводы', icon: '💸', badge: withdrawals.filter(w => w.status === 'pending').length || undefined },
    { key: 'crypto', label: 'CryptoBot', icon: '💰' },
  ]

  return (
    <div className="page">
      <UserHeader />

      <div className="header" style={{ padding: '0 0 12px 0' }}>
        <h1>⚙️ Панель управления</h1>
        <p style={{ fontSize: 12, color: '#6b7280' }}>Баланс: {balance.toFixed(2)} ₽</p>
      </div>

      <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap' }}>
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            style={{
              padding: '8px 14px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 600,
              background: tab === t.key ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.05)',
              color: tab === t.key ? '#a5b4fc' : '#6b7280', position: 'relative',
            }}>
            {t.icon} {t.label}
            {t.badge ? <span style={{ marginLeft: 4, background: '#f87171', color: '#fff', borderRadius: 10, padding: '1px 6px', fontSize: 10 }}>{t.badge}</span> : null}
          </button>
        ))}
      </div>

      {msg && (
        <div style={{
          background: msg.startsWith('✅') ? 'rgba(52,211,153,0.1)' : 'rgba(248,113,113,0.1)',
          border: '1px solid ' + (msg.startsWith('✅') ? 'rgba(52,211,153,0.2)' : 'rgba(248,113,113,0.2)'),
          color: msg.startsWith('✅') ? '#34d399' : '#f87171',
          fontSize: 13, padding: '10px 14px', borderRadius: 10, marginBottom: 12,
        }}>{msg}</div>
      )}

      <button className="glass-btn-secondary" style={{ padding: '4px 12px', fontSize: 11, marginBottom: 12 }} onClick={loadData}>
        🔄 Обновить
      </button>

      {tab === 'dashboard' && (
        <>
          <div className="stat-grid" style={{ marginBottom: 16 }}>
            <div className="stat-item"><div className="value">{dash?.users ?? '—'}</div><div className="label">Пользователи</div></div>
            <div className="stat-item"><div className="value">{dash?.channels ?? '—'}</div><div className="label">Каналы всего</div></div>
            <div className="stat-item"><div className="value" style={{ color: '#fbbf24' }}>{dash?.pending_channels ?? '—'}</div><div className="label">На модерации</div></div>
            <div className="stat-item"><div className="value" style={{ color: '#34d399' }}>{dash?.active_channels ?? '—'}</div><div className="label">Активных</div></div>
            <div className="stat-item"><div className="value">{dash?.orders ?? '—'}</div><div className="label">Заказы всего</div></div>
            <div className="stat-item"><div className="value" style={{ color: '#fbbf24' }}>{dash?.pending_orders ?? '—'}</div><div className="label">В ожидании</div></div>
            <div className="stat-item"><div className="value" style={{ color: '#34d399' }}>{dash?.active_orders ?? '—'}</div><div className="label">Активных</div></div>
            <div className="stat-item"><div className="value">{dash?.channels && dash?.active_channels ? ((dash.active_channels / dash.channels) * 100).toFixed(0) : '—'}%</div><div className="label">Конверсия</div></div>
          </div>

          {withdrawals.filter(w => w.status === 'pending').length > 0 && (
            <div className="glass-card" style={{ marginBottom: 16, padding: 14, border: '1px solid rgba(248,113,113,0.3)' }}>
              <div style={{ fontSize: 13, color: '#f87171', marginBottom: 8, fontWeight: 600 }}>
                ⚠️ {withdrawals.filter(w => w.status === 'pending').length} заявок на вывод ожидают
              </div>
              <button className="glass-btn" style={{ padding: '6px 14px', fontSize: 12 }} onClick={() => setTab('withdrawals')}>
                Перейти к выводам
              </button>
            </div>
          )}

          {pending.length > 0 && (
            <div className="glass-card" style={{ marginBottom: 16, padding: 14, border: '1px solid rgba(251,191,36,0.3)' }}>
              <div style={{ fontSize: 13, color: '#fbbf24', marginBottom: 8, fontWeight: 600 }}>
                🆕 {pending.length} каналов ожидают модерации
              </div>
              <button className="glass-btn" style={{ padding: '6px 14px', fontSize: 12 }} onClick={() => setTab('moderation')}>
                Перейти к модерации
              </button>
            </div>
          )}
        </>
      )}

      {tab === 'moderation' && (
        <>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 12 }}>
            На модерации: {pending.length}
          </div>
          {pending.length === 0 ? (
            <div className="empty-state"><div className="empty-icon">✅</div><h3>Нет каналов на проверке</h3></div>
          ) : (
            pending.map(ch => (
              <div key={ch.id} className="glass-card" style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 16, fontWeight: 600, color: '#f0f0ff', marginBottom: 4 }}>{ch.title}</div>
                <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 8 }}>
                  @{ch.username || '—'} · {ch.price_per_post ?? '—'} ₽ · Владелец: {ch.owner_id}
                  {ch.categories && <span> · {ch.categories}</span>}
                  {ch.subscribers_count && <span> · 👥 {ch.subscribers_count.toLocaleString()}</span>}
                </div>
                {ch.description && (
                  <div style={{ fontSize: 13, color: '#a0a0c0', marginBottom: 12, lineHeight: 1.4 }}>{ch.description}</div>
                )}
                <div style={{ display: 'flex', gap: 10 }}>
                  <button className="glass-btn" style={{ flex: 1, padding: '8px 0', fontSize: 13 }} onClick={() => moderate(ch.id, true)}>✅ Одобрить</button>
                  <button className="glass-btn-secondary" style={{ flex: 1, padding: '8px 0', fontSize: 13, color: '#f87171', borderColor: 'rgba(248,113,113,0.3)' }} onClick={() => moderate(ch.id, false)}>❌ Отклонить</button>
                </div>
              </div>
            ))
          )}
        </>
      )}

      {tab === 'channels' && (
        <>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 12 }}>
            Всего: {allChannels.length} · Активных: {allChannels.filter(c => c.is_active).length} · На модерации: {pending.length} · Отклонено: {allChannels.filter(c => c.is_moderated && !c.is_active).length}
          </div>
          {allChannels.length === 0 ? (
            <div className="empty-state"><div className="empty-icon">📭</div><h3>Нет каналов</h3></div>
          ) : (
            allChannels.map(ch => (
              <div key={ch.id} className="glass-card" style={{ marginBottom: 8, padding: '12px 16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: '#f0f0ff' }}>
                      {ch.title}
                      <span style={{
                        marginLeft: 8, fontSize: 10, padding: '2px 6px', borderRadius: 6,
                        background: ch.is_active ? 'rgba(52,211,153,0.15)' : 'rgba(248,113,113,0.15)',
                        color: ch.is_active ? '#34d399' : '#f87171',
                      }}>
                        {ch.is_active ? 'активен' : ch.is_moderated ? 'отклонён' : 'ожидает'}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>
                      #{ch.id} · @{ch.username || '—'} · {ch.price_per_post ?? '—'} ₽ · Владелец: {ch.owner_id}
                    </div>
                    {ch.subscribers_count && (
                      <div style={{ fontSize: 11, color: '#818cf8', marginTop: 2 }}>
                        👥 {ch.subscribers_count.toLocaleString()} подписчиков
                      </div>
                    )}
                    {ch.description && (
                      <div style={{ fontSize: 12, color: '#a0a0c0', marginTop: 4, lineHeight: 1.3 }}>{ch.description.slice(0, 100)}{ch.description.length > 100 ? '...' : ''}</div>
                    )}
                  </div>
                  {!ch.is_moderated && (
                    <div style={{ display: 'flex', gap: 6, flexShrink: 0, marginLeft: 8 }}>
                      <button className="glass-btn" style={{ padding: '4px 10px', fontSize: 11 }} onClick={() => moderate(ch.id, true)}>✅</button>
                      <button className="glass-btn-secondary" style={{ padding: '4px 10px', fontSize: 11, color: '#f87171', borderColor: 'rgba(248,113,113,0.3)' }} onClick={() => moderate(ch.id, false)}>❌</button>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </>
      )}

      {tab === 'withdrawals' && (
        <>
          {withdrawals.length === 0 ? (
            <div className="empty-state"><div className="empty-icon">📭</div><h3>Нет заявок на вывод</h3></div>
          ) : (
            withdrawals.map(w => (
              <div key={w.id} className="glass-card" style={{ marginBottom: 8, padding: '12px 16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: 14, color: '#f0f0ff' }}>#{w.id} · Пользователь {w.user_id}</div>
                    <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>
                      {new Date(w.created_at).toLocaleString('ru')}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{w.amount.toFixed(2)} ₽</div>
                    <div style={{ fontSize: 11, color: '#6b7280' }}>комиссия: {w.fee.toFixed(2)} ₽</div>
                    <div style={{ fontSize: 11, color: w.status === 'completed' ? '#34d399' : w.status === 'pending' ? '#fbbf24' : '#f87171', textTransform: 'uppercase' }}>
                      {w.status === 'completed' ? 'Выполнен' : w.status === 'pending' ? 'Ожидает' : w.status}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </>
      )}

      {tab === 'crypto' && (
        <div className="glass-card" style={{ padding: 16 }}>
          <div style={{ fontSize: 14, color: '#a0a0c0', marginBottom: 8 }}>💰 CryptoBot</div>
          <div style={{ fontSize: 32, fontWeight: 700, color: '#f0f0ff', marginBottom: 10 }}>
            {cryptoBalance !== null ? cryptoBalance.toFixed(2) + ' USDT' : '—'}
            <button className="glass-btn-secondary" style={{ marginLeft: 10, padding: '4px 10px', fontSize: 12 }} onClick={() => {
              apiFetch<{ balance: any }>('/api/admin/cryptobot-balance')
                .then(d => setCryptoBalance(d.balance?.[0]?.available ?? 0)).catch(() => {})
            }}>🔄</button>
          </div>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 12 }}>
            Курс: 1 USDT ≈ {cryptoBalance && balance ? (balance / cryptoBalance).toFixed(0) : '—'} ₽
          </div>
          <button className="glass-btn" style={{ width: '100%', padding: '10px 0', fontSize: 13 }} onClick={setupWebhook}>
            🔗 Настроить вебхук CryptoBot
          </button>
          {webhookStatus && (
            <div style={{ fontSize: 12, marginTop: 8, color: webhookStatus.startsWith('✅') ? '#34d399' : '#f87171', wordBreak: 'break-all' }}>
              {webhookStatus}
            </div>
          )}
        </div>
      )}
    </div>
  )
}