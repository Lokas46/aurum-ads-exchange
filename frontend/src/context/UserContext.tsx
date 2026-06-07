import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react'
import { getInitData, getTgUser, expandApp } from '../api/telegram'
import { apiFetch, UserProfile } from '../api/client'

interface UserState {
  profile: UserProfile | null
  tgUser: { id: number; first_name: string } | null
  balance: number
  balanceLoading: boolean
  isAuthReady: boolean
  refreshBalance: () => Promise<void>
  updateProfile: (data: { first_name?: string; username?: string }) => Promise<void>
}

const UserContext = createContext<UserState>({
  profile: null,
  tgUser: null,
  balance: 0,
  balanceLoading: false,
  isAuthReady: false,
  refreshBalance: async () => {},
  updateProfile: async () => {},
})

export function UserProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [tgUser, setTgUser] = useState<{ id: number; first_name: string } | null>(null)
  const [balance, setBalance] = useState(0)
  const [balanceLoading, setBalanceLoading] = useState(false)
  const [isAuthReady, setIsAuthReady] = useState(false)

  useEffect(() => {
    expandApp()
    const fromSdk = getTgUser()
    if (fromSdk) {
      setTgUser({
        id: fromSdk.id,
        first_name: fromSdk.first_name || '',
      })
    }

    const initData = getInitData()
    const devId = sessionStorage.getItem('dev_user_id')

    if (initData || devId) {
      apiFetch<UserProfile>('/api/users/me')
        .then(prof => {
          setProfile(prof)
          setTgUser({ id: prof.id, first_name: prof.first_name || '' })
          setBalance(prof.balance_rub)
          setIsAuthReady(true)
        })
        .catch(() => setIsAuthReady(true))
    } else {
      setIsAuthReady(true)
    }
  }, [])

  const refreshBalance = useCallback(async () => {
    if (!profile && !tgUser) return
    setBalanceLoading(true)
    try {
      const data = await apiFetch<UserProfile>('/api/users/me')
      setProfile(data)
      setBalance(data.balance_rub)
    } catch (e) {
      console.error('refreshBalance error:', e)
    }
    setBalanceLoading(false)
  }, [profile, tgUser])

  const updateProfileFn = useCallback(async (data: { first_name?: string; username?: string }) => {
    try {
      await apiFetch('/api/users/me', {
        method: 'PATCH',
        body: JSON.stringify(data),
      })
      await refreshBalance()
    } catch (e) {
      console.error('updateProfile error:', e)
    }
  }, [refreshBalance])

  return (
    <UserContext.Provider value={{
      profile,
      tgUser,
      balance,
      balanceLoading,
      isAuthReady,
      refreshBalance,
      updateProfile: updateProfileFn,
    }}>
      {children}
    </UserContext.Provider>
  )
}

export const useUser = () => useContext(UserContext)
