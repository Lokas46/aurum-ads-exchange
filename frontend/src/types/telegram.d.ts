export {}

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initDataUnsafe: {
          user?: TgUser
          query_id?: string
        }
        initData: string
        ready: () => void
        expand: () => void
        close: () => void
        HapticFeedback?: {
          impactOccurred: (style: 'light' | 'medium' | 'heavy') => void
        }
        showAlert: (msg: string) => void
        showConfirm: (msg: string, callback?: (ok: boolean) => void) => void
        MainButton: {
          setText: (text: string) => void
          show: () => void
          hide: () => void
          onClick: (cb: () => void) => void
          enable: () => void
          disable: () => void
        }
        colorScheme: string
        themeParams: Record<string, string>
        openLink?: (url: string, options?: { try_instant_view?: boolean }) => void
      }
    }
  }
}

export interface TgUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
  language_code?: string
}
