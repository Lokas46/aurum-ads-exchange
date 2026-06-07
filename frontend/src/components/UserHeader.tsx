import { useState } from 'react'
import { useUser } from '../context/UserContext'
export default function UserHeader() {
  const { tgUser, balance, updateProfile } = useUser()
  const [editing, setEditing] = useState(false)
  const [editName, setEditName] = useState('')

  if (!tgUser) {
    return null
  }

  const name = tgUser.first_name?.trim() ? tgUser.first_name : `User #${tgUser.id}`
  const initial = name[0].toUpperCase()

  const handleSaveName = async () => {
    const trimmed = editName.trim()
    if (trimmed && trimmed !== tgUser.first_name) {
      await updateProfile({ first_name: trimmed })
    }
    setEditing(false)
  }

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      background: 'rgba(255,255,255,0.03)', borderRadius: 12,
      border: '1px solid rgba(255,255,255,0.05)',
      padding: '8px 12px', marginBottom: 16,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1 }}>
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: 'linear-gradient(135deg, #818cf8, #c084fc)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontWeight: 700, fontSize: 13, flexShrink: 0,
        }}>
          {initial}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          {editing ? (
            <div style={{ display: 'flex', gap: 6 }}>
              <input
                value={editName}
                onChange={e => setEditName(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleSaveName() }}
                style={{
                  flex: 1, padding: '6px 10px', borderRadius: 8, border: '1px solid rgba(99,102,241,0.4)',
                  background: 'rgba(0,0,0,0.3)', color: '#fff', fontSize: 13, outline: 'none',
                }}
                autoFocus
                placeholder="Введите имя"
              />
              <button onClick={handleSaveName} style={{
                padding: '6px 12px', borderRadius: 8, border: 'none', cursor: 'pointer',
                background: 'rgba(99,102,241,0.4)', color: '#a5b4fc', fontWeight: 600, fontSize: 12,
              }}>OK</button>
              <button onClick={() => setEditing(false)} style={{
                padding: '6px 10px', borderRadius: 8, border: 'none', cursor: 'pointer',
                background: 'rgba(255,255,255,0.06)', color: '#9ca3af', fontSize: 12,
              }}>×</button>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: '#f0f0ff', cursor: 'default' }}>
                {name}
              </span>
              <button
                onClick={() => { setEditName(tgUser.first_name === `User #${tgUser.id}` ? '' : tgUser.first_name); setEditing(true) }}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer', padding: 2,
                  color: '#6b7280', fontSize: 11, lineHeight: 1,
                }}
                title="Редактировать имя"
              >
                ✎
              </button>
            </div>
          )}
        </div>
      </div>
      <div style={{
        background: 'rgba(52,211,153,0.1)', borderRadius: 8,
        padding: '4px 10px', fontSize: 13, fontWeight: 600, color: '#34d399',
      }}>
        {balance.toFixed(2)} ₽
      </div>
    </div>
  )
}
