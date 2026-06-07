import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchChannels, Channel } from '../api/client'
import { hapticFeedback } from '../api/telegram'
import UserHeader from '../components/UserHeader'

const ALL_CATEGORIES = [
  'крипта', 'трейдинг', 'новости', 'it', 'бизнес', 'маркетинг',
  'образование', 'юмор', 'игры', 'спорт', 'здоровье', 'мода',
  'путешествия', 'еда', 'искусство', 'музыка', 'кино',
]

export default function Catalog() {
  const [channels, setChannels] = useState<Channel[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [selectedCat, setSelectedCat] = useState('')
  const [sortBy, setSortBy] = useState<'price' | 'subs' | ''>('')
  const navigate = useNavigate()

  useEffect(() => {
    fetchChannels()
      .then((data: Channel[]) => { setChannels(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const filtered = channels.filter(ch => {
    if (search && !ch.title.toLowerCase().includes(search.toLowerCase())) return false
    if (selectedCat && !ch.categories?.split(',').map(c => c.trim()).includes(selectedCat)) return false
    return true
  }).sort((a, b) => {
    if (sortBy === 'price') return (a.price_per_post ?? 999999) - (b.price_per_post ?? 999999)
    if (sortBy === 'subs') return (b.subscribers_count ?? 0) - (a.subscribers_count ?? 0)
    return 0
  })

  if (loading) {
    return <div className="page"><div className="loading">Загрузка каналов</div></div>
  }

  return (
    <div className="page">
      <UserHeader />
      <div className="header" style={{ padding: '0 0 12px 0' }}>
        <h1>Каталог</h1>
        <p>Выбери канал для рекламы</p>
      </div>

      <div className="glass-card" style={{ marginBottom: 12, padding: 12 }}>
        <input type="text" placeholder="🔍 Поиск каналов..." value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ width: '100%', background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 10, padding: '10px 14px', color: '#e0e0e0', fontSize: 14, outline: 'none' }}
        />
        <div style={{ display: 'flex', gap: 6, marginTop: 10, flexWrap: 'wrap' }}>
          <button onClick={() => { setSelectedCat(''); setSortBy('') }}
            style={{ background: !selectedCat && !sortBy ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '4px 10px',
              color: '#e0e0e0', fontSize: 12, cursor: 'pointer' }}>Все</button>
          <button onClick={() => setSortBy('price')}
            style={{ background: sortBy === 'price' ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '4px 10px',
              color: '#e0e0e0', fontSize: 12, cursor: 'pointer' }}>↓ Цена</button>
          <button onClick={() => setSortBy('subs')}
            style={{ background: sortBy === 'subs' ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '4px 10px',
              color: '#e0e0e0', fontSize: 12, cursor: 'pointer' }}>↓ Подписчики</button>
        </div>
        <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
          {ALL_CATEGORIES.map(cat => (
            <button key={cat} onClick={() => setSelectedCat(selectedCat === cat ? '' : cat)}
              className="category-tag" style={{
                background: selectedCat === cat ? 'rgba(99,102,241,0.3)' : 'rgba(99,102,241,0.12)',
                border: selectedCat === cat ? '1px solid rgba(99,102,241,0.5)' : '1px solid rgba(99,102,241,0.2)',
                color: selectedCat === cat ? '#a5b4fc' : '#818cf8',
                fontSize: 11, padding: '3px 10px', borderRadius: 8, cursor: 'pointer',
              }}>{cat}</button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state"><div className="empty-icon">📭</div><h3>Ничего не найдено</h3></div>
      ) : (
        filtered.map(ch => (
          <div key={ch.id} className="glass-card" style={{ cursor: 'pointer', marginBottom: 10 }}
            onClick={() => { hapticFeedback('light'); navigate(`/miniapp/channel/${ch.id}`) }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <span style={{ fontSize: 16, fontWeight: 600, color: '#f0f0ff' }}>
                {ch.title}
                {ch.is_verified && <span style={{ marginLeft: 6, color: '#34d399' }}>✓</span>}
              </span>
              <span className="price">{ch.price_per_post ?? '—'} ₽</span>
            </div>
            <div className="meta" style={{ fontSize: 12 }}>
              {ch.subscribers_count && <span>👥 {ch.subscribers_count.toLocaleString()}</span>}
            </div>
            {ch.categories && (
              <div style={{ display: 'flex', gap: 4, marginTop: 6, flexWrap: 'wrap' }}>
                {ch.categories.split(',').map((c, i) => (
                  <span key={i} className="category-tag" style={{
                    background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.2)',
                    color: '#818cf8', fontSize: 10, padding: '2px 7px', borderRadius: 5
                  }}>{c.trim()}</span>
                ))}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  )
}
