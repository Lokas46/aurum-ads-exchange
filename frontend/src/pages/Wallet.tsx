import { useEffect, useState } from 'react'
import { useUser } from '../context/UserContext'
import { fetchTransactions, depositCryptoBot, withdrawFunds, Transaction } from '../api/client'
import UserHeader from '../components/UserHeader'

type WalletTab = 'info' | 'deposit' | 'withdraw'
type PaymentMethod = 'cryptobot' | 'kassy' | 'platega'

const PAYMENT_METHODS: { id: PaymentMethod; label: string; active: boolean; color: string }[] = [
  { id: 'cryptobot', label: 'CryptoBot', active: true, color: '#34d399' },
  { id: 'kassy', label: 'Kassy.ai', active: false, color: '#f87171' },
  { id: 'platega', label: 'Platega', active: false, color: '#f87171' },
]

export default function Wallet() {
  const { balance, refreshBalance } = useUser()
  const [txns, setTxns] = useState<Transaction[]>([])
  const [tab, setTab] = useState<WalletTab>('info')
  const [method, setMethod] = useState<PaymentMethod>('cryptobot')
  const [depositAmount, setDepositAmount] = useState('')
  const [depositing, setDepositing] = useState(false)
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [withdrawing, setWithdrawing] = useState(false)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    fetchTransactions()
      .then(data => setTxns(data))
      .catch(() => {})
  }, [])

  async function handleDeposit() {
    const amt = parseFloat(depositAmount)
    if (!amt || amt < 1) {
      setMsg('❌ Минимум 1 USDT')
      return
    }
    setDepositing(true)
    setMsg('')
    try {
      const data = await depositCryptoBot(amt)
      const tg = window.Telegram?.WebApp
      try {
        if (tg?.openLink) tg.openLink(data.pay_url, { try_instant_view: false })
        else window.open(data.pay_url, '_blank')
      } catch {
        window.open(data.pay_url, '_blank')
      }
      setMsg(`✅ Счёт создан! Перейди по ссылке и оплати`)
      setDepositAmount('')
    } catch (e: any) {
      setMsg(`❌ Ошибка: ${e?.message || 'неизвестная'}`)
    }
    setDepositing(false)
  }

  async function handleWithdraw() {
    const amt = parseFloat(withdrawAmount)
    if (!amt || amt < 500) {
      setMsg('❌ Минимум 500 ₽')
      return
    }
    if (amt > balance) {
      setMsg('❌ Недостаточно средств')
      return
    }
    setWithdrawing(true)
    setMsg('')
    try {
      const data = await withdrawFunds(amt)
      setMsg(`✅ Заявка #${data.withdrawal_id} создана! Статус: ${data.status}`)
      await refreshBalance()
      setWithdrawAmount('')
    } catch (e: any) {
      setMsg(`❌ Ошибка: ${e?.message || ''}`)
    }
    setWithdrawing(false)
  }

  return (
    <div className="page">
      <UserHeader />

      <div className="glass-card" style={{ textAlign: 'center', padding: '32px 20px', marginBottom: 16 }}>
        <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 8 }}>Баланс</div>
        <div style={{ fontSize: 40, fontWeight: 700, color: '#f0f0ff', marginBottom: 4 }}>
          {balance.toFixed(2)}
        </div>
        <div style={{ fontSize: 14, color: '#34d399', fontWeight: 600 }}>₽</div>
      </div>

      {msg && (
        <div style={{
          background: msg.startsWith('✅') ? 'rgba(52,211,153,0.1)' : 'rgba(248,113,113,0.1)',
          border: `1px solid ${msg.startsWith('✅') ? 'rgba(52,211,153,0.2)' : 'rgba(248,113,113,0.2)'}`,
          color: msg.startsWith('✅') ? '#34d399' : '#f87171',
          fontSize: 13, padding: '10px 14px', borderRadius: 10, marginBottom: 12, wordBreak: 'break-all',
        }}>{msg}</div>
      )}

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <button onClick={() => setTab('deposit')}
          style={{ flex: 1, padding: '10px 0', borderRadius: 10, border: 'none', cursor: 'pointer',
            background: tab === 'deposit' ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.05)',
            color: tab === 'deposit' ? '#a5b4fc' : '#6b7280', fontWeight: 600, fontSize: 13 }}>
          💳 Пополнить
        </button>
        <button onClick={() => setTab('withdraw')}
          style={{ flex: 1, padding: '10px 0', borderRadius: 10, border: 'none', cursor: 'pointer',
            background: tab === 'withdraw' ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.05)',
            color: tab === 'withdraw' ? '#a5b4fc' : '#6b7280', fontWeight: 600, fontSize: 13 }}>
          💸 Вывести
        </button>
      </div>

      {tab === 'deposit' && (
        <>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            {PAYMENT_METHODS.map(pm => (
              <button key={pm.id} onClick={() => pm.active && setMethod(pm.id)}
                style={{
                  flex: 1, padding: '12px 6px', borderRadius: 10, cursor: pm.active ? 'pointer' : 'not-allowed',
                  border: method === pm.id ? `2px solid ${pm.color}` : '2px solid rgba(255,255,255,0.06)',
                  background: method === pm.id ? `${pm.color}15` : 'rgba(255,255,255,0.03)',
                  opacity: pm.active ? 1 : 0.5, textAlign: 'center', transition: 'all 0.2s',
                }}>
                <div style={{ fontSize: 20, marginBottom: 4 }}>
                  {pm.id === 'cryptobot' ? '💰' : pm.id === 'kassy' ? '💳' : '🏦'}
                </div>
                <div style={{ fontSize: 11, fontWeight: 600, color: pm.active ? '#e0e0f0' : '#6b7280' }}>{pm.label}</div>
                <div style={{ fontSize: 9, color: pm.color, marginTop: 2 }}>
                  {pm.active ? 'активно' : 'скоро'}
                </div>
              </button>
            ))}
          </div>

          {method === 'cryptobot' && (
            <div className="glass-card" style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 13, color: '#a0a0c0', marginBottom: 8 }}>
                Введи сумму в USDT. Курс: 1 USDT ~ 90 ₽. Минимум: 1 USDT.
              </div>
              <input type="number" placeholder="Сумма в USDT" value={depositAmount}
                onChange={e => setDepositAmount(e.target.value)}
                style={{ width: '100%', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 10, padding: '12px 14px', color: '#e0e0e0', fontSize: 16, outline: 'none', marginBottom: 10 }}
              />
              <button className="glass-btn" style={{ width: '100%' }} onClick={handleDeposit} disabled={depositing}>
                {depositing ? 'Создание счёта...' : '💳 Оплатить через CryptoBot'}
              </button>
              <button className="glass-btn-secondary" style={{ width: '100%', marginTop: 8 }}
                onClick={async () => { setMsg('🔄 Проверка...'); await refreshBalance(); setMsg('✅ Баланс обновлён') }}>
                🔄 Проверить баланс
              </button>
            </div>
          )}

          {method === 'kassy' && (
            <div className="glass-card" style={{ marginBottom: 12, opacity: 0.6 }}>
              <div style={{ fontSize: 13, color: '#f87171', marginBottom: 4 }}>Kassy.ai — временно недоступен</div>
              <div style={{ fontSize: 12, color: '#6b7280' }}>Карты РФ, СБП — скоро</div>
            </div>
          )}

          {method === 'platega' && (
            <div className="glass-card" style={{ marginBottom: 12, opacity: 0.6 }}>
              <div style={{ fontSize: 13, color: '#f87171', marginBottom: 4 }}>Platega — временно недоступен</div>
              <div style={{ fontSize: 12, color: '#6b7280' }}>СБП по РФ — скоро</div>
            </div>
          )}
        </>
      )}

      {tab === 'withdraw' && (
        <div className="glass-card" style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 14, color: '#a0a0c0', marginBottom: 8 }}>
            Вывод средств
          </div>
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 12, lineHeight: 1.5 }}>
            Вывод на CryptoBot (USDT). Минимальная сумма: 500 ₽.
          </div>
          <input type="number" placeholder="Сумма в ₽" value={withdrawAmount}
            onChange={e => setWithdrawAmount(e.target.value)}
            style={{ width: '100%', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 10, padding: '12px 14px', color: '#e0e0e0', fontSize: 16, outline: 'none', marginBottom: 10 }}
          />
          <button className="glass-btn" style={{ width: '100%' }} onClick={handleWithdraw} disabled={withdrawing}>
            {withdrawing ? 'Отправка...' : '💸 Вывести'}
          </button>
        </div>
      )}

      <div style={{ fontSize: 13, color: '#6b7280', marginTop: 16, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        История
      </div>

      {txns.length === 0 ? (
        <div className="empty-state" style={{ padding: '20px' }}>
          <p>Транзакций пока нет</p>
        </div>
      ) : (
        txns.map(tx => (
          <div key={tx.id} className="glass-card" style={{ marginBottom: 6, padding: '12px 16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 14, color: '#f0f0ff' }}>{tx.description || tx.type}</div>
                <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>
                  {new Date(tx.created_at).toLocaleDateString('ru')}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontWeight: 600, color: tx.type === 'deposit' ? '#34d399' : '#f87171' }}>
                  {tx.type === 'deposit' ? '+' : '-'}{tx.amount} ₽
                </div>
                <div style={{ fontSize: 11, color: tx.status === 'completed' ? '#34d399' : '#fbbf24' }}>
                  {tx.status === 'completed' ? 'Выполнено' : tx.status === 'pending' ? 'В обработке' : tx.status}
                </div>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  )
}