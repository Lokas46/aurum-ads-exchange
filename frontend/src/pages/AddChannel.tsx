import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { hapticFeedback } from '../api/telegram'
import { createChannel } from '../api/client'
import UserHeader from '../components/UserHeader'

const ALL_CATEGORIES = [
  'крипта', 'трейдинг', 'новости', 'it', 'бизнес', 'маркетинг',
  'образование', 'юмор', 'игры', 'спорт', 'здоровье', 'мода',
  'путешествия', 'еда', 'искусство', 'музыка', 'кино',
]

type Step = 'username' | 'description' | 'price' | 'categories' | 'done'

export default function AddChannel() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('username')
  const [username, setUsername] = useState('')
  const [description, setDescription] = useState('')
  const [price, setPrice] = useState('')
  const [categories, setCategories] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  function toggleCat(cat: string) {
    setCategories(prev =>
      prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]
    )
  }

  function canNext(): boolean {
    if (step === 'username') return username.trim().length > 0
    if (step === 'description') return description.trim().length >= 10
    if (step === 'price') return parseFloat(price) > 0
    if (step === 'categories') return categories.length > 0
    return true
  }

  async function handleSubmit() {
    setSubmitting(true)
    setError('')
    try {
      const res = await createChannel({
        title: `@${username.replace('@', '')}`,
        username: username.replace('@', ''),
        description,
        price_per_post: parseFloat(price),
        categories: categories.join(', '),
      })
      if (res.ok) {
        hapticFeedback('medium')
        setStep('done')
      } else {
        setError('Ошибка при создании канала')
      }
    } catch (e: any) {
      setError(e?.message || 'Ошибка сети')
    }
    setSubmitting(false)
  }

  function renderStep() {
    switch (step) {
      case 'username':
        return (
          <div className="glass-card" style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 14, color: '#a0a0c0', marginBottom: 8 }}>Шаг 1 из 4</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#f0f0ff', marginBottom: 12 }}>
              @username канала
            </div>
            <input type="text" placeholder="например: my_channel" value={username}
              onChange={e => setUsername(e.target.value)}
              style={{ width: '100%', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 10, padding: '12px 14px', color: '#e0e0e0', fontSize: 16, outline: 'none', marginBottom: 12 }}
            />
            <div style={{ fontSize: 12, color: '#6b7280', lineHeight: 1.5 }}>
              Убедись, что бот @aurumads_bot добавлен в канал как администратор.
            </div>
          </div>
        )
      case 'description':
        return (
          <div className="glass-card" style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 14, color: '#a0a0c0', marginBottom: 8 }}>Шаг 2 из 4</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#f0f0ff', marginBottom: 12 }}>
              Описание канала
            </div>
            <textarea placeholder="О чём канал? Чем интересен рекламодателям?" value={description}
              onChange={e => setDescription(e.target.value)} rows={4}
              style={{ width: '100%', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 10, padding: '12px 14px', color: '#e0e0e0', fontSize: 14, outline: 'none', marginBottom: 12, resize: 'none' }}
            />
          </div>
        )
      case 'price':
        return (
          <div className="glass-card" style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 14, color: '#a0a0c0', marginBottom: 8 }}>Шаг 3 из 4</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#f0f0ff', marginBottom: 12 }}>
              Цена за рекламный пост
            </div>
            <input type="number" placeholder="Например: 500" value={price}
              onChange={e => setPrice(e.target.value)}
              style={{ width: '100%', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 10, padding: '12px 14px', color: '#e0e0e0', fontSize: 16, outline: 'none', marginBottom: 8 }}
            />
            <div style={{ fontSize: 12, color: '#6b7280' }}>Цена в рублях (₽)</div>
          </div>
        )
      case 'categories':
        return (
          <div className="glass-card" style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 14, color: '#a0a0c0', marginBottom: 8 }}>Шаг 4 из 4</div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#f0f0ff', marginBottom: 12 }}>
              Категории
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {ALL_CATEGORIES.map(cat => (
                <button key={cat} onClick={() => toggleCat(cat)}
                  style={{
                    padding: '8px 14px', borderRadius: 8, border: '1px solid',
                    background: categories.includes(cat) ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.04)',
                    borderColor: categories.includes(cat) ? 'rgba(99,102,241,0.5)' : 'rgba(255,255,255,0.08)',
                    color: categories.includes(cat) ? '#a5b4fc' : '#6b7280',
                    fontSize: 13, cursor: 'pointer', transition: 'all 0.2s',
                  }}>
                  {cat}
                </button>
              ))}
            </div>
          </div>
        )
      case 'done':
        return (
          <div className="glass-card" style={{ textAlign: 'center', padding: '40px 20px' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
            <h3 style={{ color: '#f0f0ff', marginBottom: 8 }}>Канал отправлен!</h3>
            <p style={{ color: '#6b7280', fontSize: 14, marginBottom: 20 }}>
              Администратор проверит его в ближайшее время.
            </p>
            <button className="glass-btn" onClick={() => navigate('/miniapp/my-channels')}>
              Мои каналы
            </button>
          </div>
        )
    }
  }

  return (
    <div className="page">
      <UserHeader />
      <div className="header" style={{ padding: '0 0 12px 0' }}>
        <button onClick={() => navigate('/miniapp/my-channels')}
          style={{ background: 'none', border: 'none', color: '#6b7280', fontSize: 14, cursor: 'pointer', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
          ← Назад
        </button>
        <h1>Добавить канал</h1>
      </div>

      {error && (
        <div style={{
          background: 'rgba(248,113,113,0.1)', border: '1px solid rgba(248,113,113,0.2)',
          color: '#f87171', fontSize: 13, padding: '10px 14px', borderRadius: 10, marginBottom: 12,
        }}>{error}</div>
      )}

      {renderStep()}

      {step !== 'done' && (
        <div style={{ display: 'flex', gap: 10 }}>
          {step !== 'username' && (
            <button className="glass-btn-secondary" style={{ flex: 1 }}
              onClick={() => {
                const map: Record<Step, Step> = { description: 'username', price: 'description', categories: 'price', username: 'username', done: 'done' }
                setStep(map[step])
              }}>
              ← Назад
            </button>
          )}
          <button className="glass-btn"
            onClick={() => {
              if (step === 'categories') { handleSubmit(); return }
              const map: Record<Step, Step> = { username: 'description', description: 'price', price: 'categories', categories: 'categories', done: 'done' }
              setStep(map[step])
            }}
            disabled={!canNext() || submitting}
            style={{ flex: 1, opacity: (!canNext() || submitting) ? 0.5 : 1, width: '100%' }}>
            {submitting ? 'Отправка...' : step === 'categories' ? '📤 Отправить на модерацию' : 'Далее →'}
          </button>
        </div>
      )}
    </div>
  )
}
