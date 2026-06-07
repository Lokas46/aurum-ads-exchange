# Deploy to Railway

## 1. Подготовка репозитория

```bash
git add .
git commit -m "Add deployment configs"
git push origin main
```

## 2. На Railway

1. **New Project** → **Deploy from GitHub repo** → выбери этот репозиторий
2. Railway автоматически найдет `railway.toml` и соберет через Dockerfile

## 3. Переменные окружения (Railway Dashboard → Variables)

Добавь все из `.env.production`:

```
BOT_TOKEN=8545667796:AAGaVvsdQg5U2O4guzOd2ZQvLJrjPZf_BMQ
DATABASE_URL=postgresql+asyncpg://postgres:password@host.railway.internal:5432/railway
API_BASE_URL=https://your-app.railway.app
WEBHOOK_BASE_URL=https://your-app.railway.app
ADMIN_IDS=[1836926514, 37175, 34175]
CRYPTOBOT_API_KEY=592676:AA0oD2QdYM5mHKlHhgJ6M6bgyDlnj9dncv7
CRYPTOBOT_USDT_RATE=90.0
COMMISSION_RATE=0.10
MIN_WITHDRAW_AMOUNT=500.0
DEBUG=false
```

**Важно:** `DATABASE_URL` — Railway сам даст при добавлении PostgreSQL сервиса.

## 4. Добавить PostgreSQL

В том же проекте: **New** → **Database** → **PostgreSQL**
Railway автоматически добавит `DATABASE_URL` в переменные.

## 5. Настроить вебхук CryptoBot

После деплоя:
```bash
# В Railway Dashboard → Variables добавь WEBHOOK_BASE_URL
# Затем в боте админом:
/setup_cryptobot
# Или curl:
curl -X POST https://your-app.railway.app/api/admin/cryptobot-setup
```

URL для вебхука: `https://your-app.railway.app/api/webhooks/cryptobot`
Настрой в @CryptoBot → Settings → Webhook URL.

## 6. Фронтенд (Mini App)

Вариант А: **Vercel** (рекомендуется в ТЗ)
- Import GitHub repo → Framework: Vite → Output: `dist`
- Env: `VITE_API_URL=https://your-app.railway.app`
- В `vercel.json` уже настроен рерайт на SPA

Вариант Б: **Railway** (в том же проекте)
- railway.toml уже настроен на сборку frontend
- Будет доступен на отдельном домене

## Локальный запуск

```bash
docker compose up -d
# API: http://localhost:8001
# Frontend: cd frontend && npm run dev
```

## Миграции

```bash
# Локально
cd backend
alembic upgrade head

# На Railway — автоматически при старте (lifespan в main.py)
```