import { getInitData } from './telegram'

const BASE_URL = ''

function headers(): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  const initData = getInitData()
  if (initData) {
    h['X-Telegram-Init-Data'] = initData
  }
  const devId = sessionStorage.getItem('dev_user_id')
  if (devId) {
    h['X-Dev-User-Id'] = devId
  }
  return h
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { ...headers(), ...options?.headers },
  })
  if (!res.ok) {
    const text = await res.text().catch(() => 'Unknown error')
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json()
}

export interface Channel {
  id: number
  title: string
  chat_id?: number
  username?: string
  invite_link?: string
  subscribers_count?: number
  price_per_post: number
  categories?: string
  description?: string
  photo_url?: string
  is_active: boolean
  is_approved: boolean
  is_moderated?: boolean
  is_verified?: boolean
  owner_id: number
}

export interface Order {
  id: number
  channel_id: number
  advertiser_id: number
  amount: number
  status: string
  post_text?: string
  created_at: string
}

export interface Transaction {
  id: number
  user_id: number
  amount: number
  type: string
  status: string
  description?: string
  created_at: string
}

export interface UserProfile {
  id: number
  username: string | null
  first_name: string
  last_name: string | null
  balance_rub: number
  hold_balance_rub: number
  role: string
  is_admin: boolean
  is_onboarded: boolean
}

export function fetchChannels(): Promise<Channel[]> {
  return apiFetch('/api/channels')
}

export function fetchChannel(id: number): Promise<Channel> {
  return apiFetch(`/api/channels/${id}`)
}

export function fetchMyProfile(): Promise<UserProfile> {
  return apiFetch('/api/users/me')
}

export function fetchBalance(): Promise<{ balance: number }> {
  return apiFetch<UserProfile>('/api/users/me').then(u => ({ balance: u.balance_rub }))
}

export function fetchOrders(): Promise<Order[]> {
  return apiFetch('/api/orders')
}

export function fetchTransactions(): Promise<Transaction[]> {
  return apiFetch('/api/transactions')
}

export function createOrder(channelId: number, postText: string): Promise<Order> {
  return apiFetch('/api/orders', {
    method: 'POST',
    body: JSON.stringify({ channel_id: channelId, post_text: postText }),
  })
}

export function createChannel(data: {
  title: string
  username: string
  description: string
  price_per_post: number
  categories: string
}): Promise<{ id: number; ok: boolean }> {
  return apiFetch('/api/channels', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function myChannels(): Promise<Channel[]> {
  return apiFetch('/api/channels/my')
}

export function depositCryptoBot(amount: number): Promise<{ pay_url: string; invoice_id: number }> {
  return apiFetch('/api/payments/deposit', {
    method: 'POST',
    body: JSON.stringify({ amount }),
  })
}

export function checkPayment(invoiceId: number): Promise<{ paid: boolean; status?: string; amount?: number }> {
  return apiFetch('/api/payments/check', {
    method: 'POST',
    body: JSON.stringify({ invoice_id: invoiceId }),
  })
}

export function withdrawFunds(amount: number): Promise<{ withdrawal_id: number; status: string }> {
  return apiFetch('/api/payments/withdraw', {
    method: 'POST',
    body: JSON.stringify({ amount }),
  })
}
