export interface TgUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
  language_code?: string
}

export function getInitData(): string {
  try {
    const initData = window.Telegram?.WebApp?.initData
    if (initData) return initData
  } catch (e) {
    console.warn('getInitData error:', e)
  }
  return ''
}

export function getTgUser(): TgUser | null {
  try {
    const tg = window.Telegram?.WebApp
    if (tg?.initDataUnsafe?.user) {
      return tg.initDataUnsafe.user
    }
  } catch (e) {
    console.warn('getTgUser error:', e)
  }
  return null
}

export function expandApp() {
  try {
    window.Telegram?.WebApp?.expand()
  } catch (e) {
    console.warn('expandApp error:', e)
  }
}

export function hapticFeedback(style: 'light' | 'medium' | 'heavy' = 'medium') {
  try {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred(style)
  } catch (e) {
    console.warn('hapticFeedback error:', e)
  }
}

export function showAlert(msg: string) {
  try {
    window.Telegram?.WebApp?.showAlert(msg)
  } catch (e) {
    console.warn('showAlert error:', e)
  }
}

export function showConfirm(msg: string): Promise<boolean> {
  return new Promise(resolve => {
    try {
      window.Telegram?.WebApp?.showConfirm(msg, (ok: boolean) => resolve(ok))
    } catch (e) {
      console.warn('showConfirm error:', e)
      resolve(true)
    }
  })
}
