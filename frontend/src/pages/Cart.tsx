import { useUser } from '../context/UserContext'

export default function Cart() {
  const { balance } = useUser()

  return (
    <div className="page">
      <div className="header">
        <h1>Корзина</h1>
        <p>Множественный заказ</p>
      </div>

      <div className="empty-state">
        <div className="empty-icon">🛒</div>
        <h3>Корзина пуста</h3>
        <p>Добавляй каналы из каталога и оформляй массовый заказ</p>
      </div>

      <div className="glass-card" style={{ marginTop: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <span style={{ color: '#6b7280', fontSize: 14 }}>Баланс</span>
          <span style={{ color: '#34d399', fontWeight: 600 }}>{balance.toFixed(2)} ₽</span>
        </div>
        <button className="glass-btn" style={{ width: '100%' }} disabled>
          Перейти к оплате
        </button>
      </div>
    </div>
  )
}
