import { useEffect, useState } from 'react'
import { useUser } from '../context/UserContext'
import { fetchOrders, Order } from '../api/client'
import UserHeader from '../components/UserHeader'

const statusMap: Record<string, { label: string; color: string }> = {
  pending: { label: 'Ожидает', color: '#fbbf24' },
  active: { label: 'Активен', color: '#34d399' },
  completed: { label: 'Завершён', color: '#818cf8' },
  cancelled: { label: 'Отменён', color: '#f87171' },
}

export default function Orders() {
  const { balance } = useUser()
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'all' | 'active'>('all')

  useEffect(() => {
    fetchOrders()
      .then(data => { setOrders(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const filtered = tab === 'active'
    ? orders.filter(o => o.status === 'pending' || o.status === 'active')
    : orders

  return (
    <div className="page">
      <UserHeader />
      <div className="header" style={{ padding: '0 0 12px 0' }}>
        <h1>Мои заказы</h1>
        <p>Всего: {orders.length} · Баланс: {balance.toFixed(2)} ₽</p>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <button onClick={() => setTab('all')}
          style={{ flex: 1, padding: '8px 0', borderRadius: 10, border: 'none', cursor: 'pointer',
            background: tab === 'all' ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.05)',
            color: tab === 'all' ? '#a5b4fc' : '#6b7280', fontWeight: 600, fontSize: 13 }}>Все</button>
        <button onClick={() => setTab('active')}
          style={{ flex: 1, padding: '8px 0', borderRadius: 10, border: 'none', cursor: 'pointer',
            background: tab === 'active' ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.05)',
            color: tab === 'active' ? '#a5b4fc' : '#6b7280', fontWeight: 600, fontSize: 13 }}>Активные</button>
      </div>

      {loading ? <div className="loading">Загрузка</div> : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <h3>Заказов пока нет</h3>
          <p>Выбери канал в каталоге и оформи заказ</p>
        </div>
      ) : (
        filtered.map(order => {
          const st = statusMap[order.status] || { label: order.status, color: '#6b7280' }
          return (
            <div key={order.id} className="glass-card" style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 600, color: '#f0f0ff', fontSize: 15 }}>Заказ #{order.id}</div>
                  <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>
                    {new Date(order.created_at).toLocaleDateString('ru')}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: '#34d399', fontWeight: 600 }}>{order.amount} ₽</div>
                  <span style={{
                    background: st.color + '22', color: st.color,
                    border: `1px solid ${st.color}44`,
                    fontSize: 11, padding: '2px 8px', borderRadius: 6, fontWeight: 600,
                  }}>{st.label}</span>
                </div>
              </div>
            </div>
          )
        })
      )}
    </div>
  )
}
