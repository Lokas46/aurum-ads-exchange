import { useNavigate, useLocation } from 'react-router-dom'
import { useUser } from '../context/UserContext'

const navItems = [
  { path: '/miniapp', icon: '📢', label: 'Каналы' },
  { path: '/miniapp/orders', icon: '📋', label: 'Заказы' },
  { path: '/miniapp/my-channels', icon: '📡', label: 'Мои' },
  { path: '/miniapp/wallet', icon: '💰', label: 'Кошелёк' },
]

export default function BottomNav() {
  const navigate = useNavigate()
  const location = useLocation()
  const { profile, balance } = useUser()

  const items = profile?.is_admin
    ? [...navItems, { path: '/miniapp/admin', icon: '⚙️', label: 'Админ' }]
    : navItems

  return (
    <nav className="bottom-nav">
      {items.map(item => (
        <button
          key={item.path}
          className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
          onClick={() => navigate(item.path)}
        >
          <span className="nav-icon">{item.icon}</span>
          <span>{item.label}</span>
          {item.path === '/miniapp/wallet' && (
            <span style={{ fontSize: 10, color: '#34d399' }}>{balance.toFixed(1)}</span>
          )}
        </button>
      ))}
    </nav>
  )
}
