import { useEffect, useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import { useUser } from './context/UserContext'
import Catalog from './pages/Catalog'
import ChannelDetail from './pages/ChannelDetail'
import Orders from './pages/Orders'
import MyChannels from './pages/MyChannels'
import Wallet from './pages/Wallet'
import Cart from './pages/Cart'
import AddChannel from './pages/AddChannel'
import Admin from './pages/Admin'
import BottomNav from './components/BottomNav'
import DevLogin from './components/DevLogin'

export default function App() {
  const { isAuthReady, profile } = useUser()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    try { window.Telegram?.WebApp?.ready() } catch {}
    setReady(true)
  }, [])

  if (!ready || !isAuthReady) return null

  if (!profile) {
    return <DevLogin />
  }

  return (
    <>
      <Routes>
        <Route path="/miniapp" element={<Catalog />} />
        <Route path="/miniapp/channel/:id" element={<ChannelDetail />} />
        <Route path="/miniapp/orders" element={<Orders />} />
        <Route path="/miniapp/my-channels" element={<MyChannels />} />
        <Route path="/miniapp/wallet" element={<Wallet />} />
        <Route path="/miniapp/cart" element={<Cart />} />
        <Route path="/miniapp/add-channel" element={<AddChannel />} />
        <Route path="/miniapp/admin" element={<Admin />} />
      </Routes>
      <BottomNav />
    </>
  )
}
