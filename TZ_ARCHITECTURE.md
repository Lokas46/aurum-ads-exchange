# Telegram Ad Exchange (Aurum Ads) — Техническое Задание и Архитектура

## 1. Обзор системы

Биржа рекламы Telegram — платформа, где владельцы каналов продают рекламные места, а рекламодатели покупают их.  
**Основной интерфейс:** Telegram Mini App (WebApp)  
**Уведомления и быстрые действия:** Telegram Bot (`@aurumads_bot`)

### Роли:
- **Рекламодатель** — создаёт кампании, пополняет баланс, выбирает каналы из каталога
- **Владелец канала** — добавляет каналы, управляет ценами, принимает/отклоняет заказы, выводит средства
- **Администратор** — модерирует каналы, управляет финансами, разрешает споры

---

## 2. Стек технологий

| Компонент | Технология | Обоснование |
|-----------|-----------|-------------|
| **Бэкенд** | Python 3.12 + FastAPI | Асинхронный, высокая производительность, встроенная документация OpenAPI |
| **Бот** | Aiogram 3.x | Лучшая асинхронная библиотека для Telegram Bot API |
| **Фронтенд (Mini App)** | React 18 + TypeScript + Vite | Быстрая разработка, строгая типизация, богатая экосистема |
| **База данных** | PostgreSQL 16 | Надёжность, full-text search, JSONB, конкурентные транзакции |
| **Платежи** | CryptoBot (USDT) + ЮKassa (RUB) | Первичный: CryptoBot (P2P USDT). Вторичный: ЮKassa (карты РФ, СБП) |
| **ORM** | SQLAlchemy 2.0 (async) | Async-нативный, поддерживает PostgreSQL + SQLite для тестов |
| **Миграции** | Alembic | Версионирование схемы БД |
| **Деплой** | Docker + Vercel (frontend proxy) | Контейнеризация, serverless edge для Mini App |

---

## 3. Архитектура базы данных

### 3.1 Таблицы

#### users
| Колонка | Тип | Ограничения | Описание |
|---------|-----|-------------|----------|
| id | BIGINT | PK | Telegram ID |
| username | VARCHAR(255) | NULL | TG username |
| first_name | VARCHAR(255) | NULL | |
| last_name | VARCHAR(255) | NULL | |
| phone | VARCHAR(32) | NULL | |
| language_code | VARCHAR(8) | NULL | |
| role | VARCHAR(20) | NOT NULL DEFAULT 'advertiser' | `advertiser`, `channel_owner`, `admin` |
| balance | DECIMAL(16,2) | NOT NULL DEFAULT 0 | Доступный баланс (RUB) |
| hold_balance | DECIMAL(16,2) | NOT NULL DEFAULT 0 | Средства в холде (эскроу) |
| is_blocked | BOOLEAN | DEFAULT FALSE | |
| is_onboarded | BOOLEAN | DEFAULT FALSE | Прошёл ли онбординг |
| created_at | TIMESTAMPTZ | DEFAULT now() | |
| updated_at | TIMESTAMPTZ | DEFAULT now() | |

**Индексы:** `idx_users_role` ON (role), `idx_users_username` ON (username)

#### channels
| Колонка | Тип | Ограничения | Описание |
|---------|-----|-------------|----------|
| id | BIGINT | PK (auto-gen) | |
| owner_id | BIGINT | FK → users.id, NOT NULL | |
| title | VARCHAR(255) | NOT NULL | |
| username | VARCHAR(255) | NULL | @username |
| chat_id | BIGINT | UNIQUE, NULL | Telegram chat_id |
| description | TEXT | NULL | |
| invite_link | VARCHAR(500) | NULL | Пригласительная ссылка |
| subscribers_count | INTEGER | NULL | |
| avg_views | INTEGER | NULL | Средние просмотры |
| avg_er | DECIMAL(5,2) | NULL | Engagement Rate (%) |
| categories | JSONB | DEFAULT '[]' | Массив категорий |
| geo | VARCHAR(100) | NULL | Гео-таргетинг |
| price_per_post | DECIMAL(12,2) | NULL | Цена за пост |
| price_per_hold | DECIMAL(12,2) | NULL | Цена за удержание в топе/ленте |
| is_verified | BOOLEAN | DEFAULT FALSE | Верифицирован админом |
| is_active | BOOLEAN | DEFAULT FALSE | Активен для показа в каталоге |
| is_moderated | BOOLEAN | DEFAULT FALSE | Прошёл модерацию |
| moderator_id | BIGINT | FK → users.id, NULL | Кто модерировал |
| moderation_comment | TEXT | NULL | |
| bot_added | BOOLEAN | DEFAULT FALSE | Бот добавлен в канал |
| last_sync_at | TIMESTAMPTZ | NULL | Последняя синхронизация статистики |
| created_at | TIMESTAMPTZ | DEFAULT now() | |
| updated_at | TIMESTAMPTZ | DEFAULT now() | |

**Индексы:**
- `idx_channels_owner` ON (owner_id)
- `idx_channels_active` ON (is_active, is_moderated) WHERE is_active = TRUE
- `idx_channels_categories` USING GIN (categories)
- `idx_channels_subscribers` ON (subscribers_count DESC)
- `idx_channels_search` — full-text search (title, description)

#### campaigns
| Колонка | Тип | Ограничения | Описание |
|---------|-----|-------------|----------|
| id | BIGINT | PK (auto-gen) | |
| advertiser_id | BIGINT | FK → users.id, NOT NULL | |
| title | VARCHAR(255) | NULL | Название кампании |
| budget | DECIMAL(14,2) | NOT NULL | Бюджет |
| post_text | TEXT | NULL | Текст рекламного поста |
| post_media | JSONB | DEFAULT '[]' | Фото/видео (S3 URLs) |
| inline_buttons | JSONB | DEFAULT '[]' | Inline-кнопки |
| schedule_date | TIMESTAMPTZ | NULL | Запланированная дата выхода |
| status | VARCHAR(30) | NOT NULL DEFAULT 'draft' | `draft → pending_payment → paid → active → completed / cancelled / disputed` |
| created_at | TIMESTAMPTZ | DEFAULT now() | |
| updated_at | TIMESTAMPTZ | DEFAULT now() | |

**Индексы:** `idx_campaigns_advertiser` ON (advertiser_id), `idx_campaigns_status` ON (status)

#### campaign_channels
| Колонка | Тип | Ограничения | Описание |
|---------|-----|-------------|----------|
| id | BIGINT | PK (auto-gen) | |
| campaign_id | BIGINT | FK → campaigns.id, NOT NULL | |
| channel_id | BIGINT | FK → channels.id, NOT NULL | |
| price | DECIMAL(12,2) | NOT NULL | Фиксированная цена для этого заказа |
| status | VARCHAR(30) | NOT NULL DEFAULT 'pending' | `pending → approved → posted → completed / rejected / disputed` |
| owner_response_deadline | TIMESTAMPTZ | NULL | Дедлайн ответа владельца (24ч) |
| owner_responded_at | TIMESTAMPTZ | NULL | |
| proof_link | VARCHAR(500) | NULL | Ссылка на опубликованный пост |
| screenshots | JSONB | DEFAULT '[]' | Скриншоты подтверждения |
| is_confirmed | BOOLEAN | DEFAULT FALSE | Рекламодатель подтвердил выход |
| confirmed_at | TIMESTAMPTZ | NULL | |
| dispute_reason | TEXT | NULL | Причина спора |
| created_at | TIMESTAMPTZ | DEFAULT now() | |
| updated_at | TIMESTAMPTZ | DEFAULT now() | |

**Уникальность:** UNIQUE (campaign_id, channel_id)  
**Индексы:** `idx_cc_channel_status` ON (channel_id, status), `idx_cc_deadline` ON (status, owner_response_deadline) WHERE status = 'pending'

#### transactions
| Колонка | Тип | Ограничения | Описание |
|---------|-----|-------------|----------|
| id | BIGINT | PK (auto-gen) | |
| user_id | BIGINT | FK → users.id, NOT NULL | |
| type | VARCHAR(30) | NOT NULL | `deposit`, `withdraw`, `hold`, `release`, `refund`, `commission` |
| amount | DECIMAL(14,2) | NOT NULL | |
| balance_before | DECIMAL(14,2) | NULL | |
| balance_after | DECIMAL(14,2) | NULL | |
| hold_before | DECIMAL(14,2) | NULL | |
| hold_after | DECIMAL(14,2) | NULL | |
| status | VARCHAR(20) | NOT NULL DEFAULT 'completed' | `pending`, `completed`, `failed` |
| external_id | VARCHAR(255) | NULL | ID в платёжной системе |
| payment_system | VARCHAR(50) | NULL | `cryptobot`, `yookassa` |
| description | TEXT | NULL | |
| reference_type | VARCHAR(50) | NULL | `campaign`, `campaign_channel`, `withdraw_request` |
| reference_id | BIGINT | NULL | |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

**Индексы:** `idx_transactions_user` ON (user_id), `idx_transactions_type` ON (type), `idx_transactions_external` ON (external_id) UNIQUE

#### withdraw_requests
| Колонка | Тип | Ограничения | Описание |
|---------|-----|-------------|----------|
| id | BIGINT | PK (auto-gen) | |
| user_id | BIGINT | FK → users.id, NOT NULL | |
| amount | DECIMAL(14,2) | NOT NULL | |
| fee | DECIMAL(14,2) | NOT NULL DEFAULT 0 | Комиссия платформы |
| net_amount | DECIMAL(14,2) | NOT NULL | Сумма к выплате |
| asset | VARCHAR(20) | NOT NULL DEFAULT 'USDT' | |
| destination_type | VARCHAR(30) | NOT NULL | `cryptobot`, `yookassa`, `card` |
| destination_details | JSONB | NOT NULL | Реквизиты |
| status | VARCHAR(20) | NOT NULL DEFAULT 'pending' | `pending → approved → completed / rejected / failed` |
| admin_id | BIGINT | FK → users.id, NULL | Кто обработал |
| external_transfer_id | VARCHAR(255) | NULL | ID трансфера в CryptoBot |
| processed_at | TIMESTAMPTZ | NULL | |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

**Индексы:** `idx_wr_status` ON (status), `idx_wr_user` ON (user_id)

#### categories
| Колонка | Тип | Ограничения |
|---------|-----|-------------|
| id | INTEGER | PK |
| name | VARCHAR(100) | NOT NULL |
| slug | VARCHAR(100) | NOT NULL UNIQUE |
| parent_id | INTEGER | FK → categories.id, NULL |
| sort_order | INTEGER | DEFAULT 0 |

#### disputes
| Колонка | Тип | Ограничения | Описание |
|---------|-----|-------------|----------|
| id | BIGINT | PK (auto-gen) | |
| campaign_channel_id | BIGINT | FK → campaign_channels.id, NOT NULL | |
| initiator_id | BIGINT | FK → users.id, NOT NULL | |
| reason | TEXT | NOT NULL | |
| status | VARCHAR(20) | NOT NULL DEFAULT 'open' | `open`, `resolved` |
| resolution | TEXT | NULL | Решение администратора |
| admin_id | BIGINT | FK → users.id, NULL | |
| created_at | TIMESTAMPTZ | DEFAULT now() | |
| resolved_at | TIMESTAMPTZ | NULL | |

#### notifications
| Колонка | Тип | Ограничения | Описание |
|---------|-----|-------------|----------|
| id | BIGINT | PK (auto-gen) | |
| user_id | BIGINT | FK → users.id, NOT NULL | |
| type | VARCHAR(50) | NOT NULL | `new_order`, `order_approved`, `order_rejected`, `order_posted`, `deposit_received`, `withdraw_status` |
| title | VARCHAR(255) | NULL | |
| body | TEXT | NULL | |
| data | JSONB | NULL | Доп. данные |
| is_read | BOOLEAN | DEFAULT FALSE | |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

**Индексы:** `idx_notif_user_read` ON (user_id, is_read)

#### channel_stats
| Колонка | Тип | Ограничения | Описание |
|---------|-----|-------------|----------|
| id | BIGINT | PK (auto-gen) | |
| channel_id | BIGINT | FK → channels.id, NOT NULL | |
| date | DATE | NOT NULL | |
| subscribers_count | INTEGER | NULL | |
| views_per_post | INTEGER | NULL | |
| reach | INTEGER | NULL | |
| estimated_er | DECIMAL(5,2) | NULL | |
| created_at | TIMESTAMPTZ | DEFAULT now() | |

**Уникальность:** UNIQUE (channel_id, date)

### 3.2 Система escrow (безопасная сделка)

```
Рекламодатель платит → средства уходят в hold_balance
  ↓
Владелец канала публикует пост → рекламодатель подтверждает
  ↓
Средства переходят владельцу канала (минус комиссия платформы)
```

**Алгоритм:**

```
1. create_campaign_channel()
   - advertiser.balance -= amount
   - advertiser.hold_balance += amount

2. approve_and_post()
   - Если владелец подтвердил и рекламодатель подтвердил выход:
     - advertiser.hold_balance -= amount
     - owner.balance += (amount - commission)
     - platform.balance += commission (внутренний счёт)

3. reject_or_refund()
   - advertiser.hold_balance -= amount
   - advertiser.balance += amount
```

**Конкурентность:** Все операции с балансом — в транзакции с `SELECT ... FOR UPDATE` на строках user.  
Порядок блокировки: всегда по возрастанию user.id для предотвращения deadlock.

### 3.3 Таймер 24 часа

Поле `campaign_channels.owner_response_deadline = NOW() + INTERVAL '24 hours'`  
Фоновая задача (каждую минуту): `SELECT ... WHERE status = 'pending' AND owner_response_deadline < NOW()` → auto-cancel с возвратом средств.

---

## 4. API Endpoints (полный список)

### Аутентификация
- Все запросы через заголовок `X-Telegram-Init-Data`
- Валидация HMAC-SHA256 + проверка `auth_date` (не старше 24ч)

### Users
| Method | Path | Описание |
|--------|------|----------|
| POST | /api/users/register | Регистрация (upsert по initData) |
| GET | /api/users/{id}/profile | Профиль |
| PATCH | /api/users/{id}/profile | Обновление профиля |
| GET | /api/users/{id}/balance | Баланс (balance + hold) |

### Channels
| Method | Path | Описание |
|--------|------|----------|
| GET | /api/channels | Каталог (активные, прошедшие модерацию) |
| GET | /api/channels/my | Мои каналы (owner_id из initData) |
| GET | /api/channels/{id} | Детали канала |
| POST | /api/channels | Создать канал |
| PATCH | /api/channels/{id} | Редактировать канал |
| DELETE | /api/channels/{id} | Деактивировать канал |
| POST | /api/channels/{id}/sync-stats | Принудительная синхронизация статистики |
| GET | /api/channels/{id}/stats | График статистики по дням |

### Campaigns
| Method | Path | Описание |
|--------|------|----------|
| GET | /api/campaigns | Список кампаний пользователя |
| POST | /api/campaigns | Создать кампанию |
| GET | /api/campaigns/{id} | Детали кампании |
| PATCH | /api/campaigns/{id} | Обновить |
| POST | /api/campaigns/{id}/pay | Оплатить (холд средств) |
| POST | /api/campaigns/{id}/cancel | Отменить |

### Campaign Channels (заказы)
| Method | Path | Описание |
|--------|------|----------|
| POST | /api/campaigns/{id}/channels | Добавить канал в кампанию |
| GET | /api/campaign-channels | Список заказов (фильтр по роли) |
| POST | /api/campaign-channels/{id}/approve | Владелец → подтвердить |
| POST | /api/campaign-channels/{id}/reject | Владелец → отклонить |
| POST | /api/campaign-channels/{id}/confirm | Рекламодатель → подтвердить выход |
| POST | /api/campaign-channels/{id}/dispute | Открыть спор |

### Payments
| Method | Path | Описание |
|--------|------|----------|
| GET | /api/payments/methods | Список доступных платёжных методов |
| POST | /api/payments/deposit | Создать счёт на пополнение |
| POST | /api/payments/check | Проверить статус инвойса |
| POST | /api/payments/withdraw | Создать заявку на вывод |
| GET | /api/payments/withdraw-requests | Мои заявки на вывод |

### Webhooks
| Method | Path | Описание |
|--------|------|----------|
| POST | /api/webhooks/cryptobot | CryptoBot callback (оплата инвойса) |
| POST | /api/webhooks/yookassa | ЮKassa callback |

### Admin
| Method | Path | Описание |
|--------|------|----------|
| GET | /api/admin/dashboard | Дашборд (KPI) |
| GET | /api/admin/channels/pending | Очередь модерации |
| POST | /api/admin/channels/{id}/moderate | Модерировать канал |
| GET | /api/admin/users | Список пользователей |
| PATCH | /api/admin/users/{id} | Управление пользователем |
| GET | /api/admin/withdraw-requests | Заявки на вывод |
| POST | /api/admin/withdraw-requests/{id}/process | Обработать вывод |
| GET | /api/admin/disputes | Список споров |
| POST | /api/admin/disputes/{id}/resolve | Разрешить спор |
| GET | /api/admin/cryptobot-balance | Баланс CryptoBot |
| GET | /api/admin/cryptobot-setup | Настройка вебхука CryptoBot |

### Transactions
| Method | Path | Описание |
|--------|------|----------|
| GET | /api/transactions | История транзакций (с пагинацией) |

---

## 5. Telegram Bot — сценарии

### Основные команды
- `/start` — регистрация, выбор роли, главное меню
- `/add_channel` — FSM: переслать сообщение из канала → описание → цена → категории
- `/wallet` — баланс, пополнение, вывод
- `/catalog` — ссылка на Mini App (каталог)
- `/my_channels` — список каналов
- `/my_orders` — список заказов

### Push-уведомления
| Событие | Кому | Текст |
|---------|------|-------|
| Новый заказ | Владелец канала | "Новый заказ на рекламу в канале {channel}. Сумма: {amount}. У вас 24ч на ответ" → inline кнопки ✅ Принять / ❌ Отклонить |
| Заказ подтверждён | Рекламодатель | "Ваш заказ в канале {channel} принят! Пост будет опубликован." |
| Заказ отклонён | Рекламодатель | "Заказ в канале {channel} отклонён. Средства возвращены." |
| Пост опубликован | Рекламодатель | "Ваш пост опубликован в канале {channel}. Подтвердите выход." → inline кнопка ✅ Подтвердить |
| Пост подтверждён | Владелец канала | "Заказ #{id} завершён. {amount} зачислено на баланс." |
| Пополнение баланса | Пользователь | "Баланс пополнен на {amount} RUB." |
| Статус вывода | Пользователь | "Заявка на вывод #{id} {одобрена/отклонена}." |

---

## 6. Mini App — структура страниц

### Маршруты
| Путь | Страница | Роль |
|------|----------|------|
| /miniapp | Catalog.tsx | Все |
| /miniapp/channel/:id | ChannelDetail.tsx | Все |
| /miniapp/my-channels | MyChannels.tsx | Владелец |
| /miniapp/add-channel | AddChannel.tsx | Владелец |
| /miniapp/campaign/:id | CampaignDetail.tsx | Рекламодатель |
| /miniapp/create-campaign | CreateCampaign.tsx (new) | Рекламодатель |
| /miniapp/orders | Orders.tsx | Все |
| /miniapp/wallet | Wallet.tsx | Все |
| /miniapp/cart | Cart.tsx (to implement) | Рекламодатель |
| /miniapp/admin | Admin.tsx | Админ |
| /miniapp/profile | Profile.tsx (new) | Все |

### Компоненты (существующие + новые)
- **UserHeader** — баланс, имя (существует)
- **BottomNav** — навигация (существует)
- **CampaignCard** — карточка кампании (новый)
- **ChannelCard** — карточка канала (существует)
- **OrderTimeline** — статусная линия заказа (новый)
- **MediaUploader** — загрузка фото/видео (новый)
- **StatusBadge** — статусный индикатор (существует частично)

---

## 7. План разработки (Roadmap)

### Спринт 0 — Подготовка (3 дня)
- [ ] Переключение с SQLite на PostgreSQL
- [ ] Инициализация Alembic
- [ ] Обновление docker-compose.yml (PostgreSQL + app)
- [ ] Добавление `asyncpg`, `aiohttp` в requirements.txt
- [ ] Настройка конфига (`.env` → `pydantic-settings`)

### Спринт 1 — Аутентификация и пользователи (1-2 недели)
- [ ] Валидация initData на бэкенде (`app/auth/telegram.py` + `deps.py`)
- [ ] FastAPI middleware/зависимость `get_current_user()`
- [ ] Роль пользователя (advertiser/channel_owner/admin)
- [ ] Онбординг: выбор роли при первом входе
- [ ] Авторегистрация при первом входе (upsert)
- [ ] Profile page (редактирование имени, просмотр баланса)
- [ ] Bot: `/start` с приветствием и кнопками по роли

### Спринт 2 — Управление каналами (1-2 недели)
- [ ] Расширение модели Channel (avg_views, avg_er, geo, bot_added)
- [ ] ChannelCategories, иерархия категорий
- [ ] Bot: FSM добавления канала (проверка, что бот — админ)
- [ ] Bot: `getChat` / `getChatMembersCount` для верификации и статистики
- [ ] API: CRUD каналов + фильтрация каталога (FTS, категории, цена, ER)
- [ ] Фоновая синхронизация статистики каналов
- [ ] Frontend: страница редактирования канала
- [ ] Frontend: улучшенный каталог с пагинацией

### Спринт 3 — Кампании и заказы (2 недели)
- [ ] Модель Campaign + CampaignChannel
- [ ] API: CRUD кампаний, добавление каналов в кампанию
- [ ] Escrow-система (hold/release/refund)
- [ ] Status Machine для заказов (pending → approved → posted → confirmed)
- [ ] Bot: уведомление владельца о новом заказе + inline Approve/Reject
- [ ] Bot: уведомление рекламодателя о результате
- [ ] Bot: фоновая задача auto-cancel по таймеру 24ч
- [ ] Frontend: конструктор кампании (текст, медиа, выбор каналов)
- [ ] Frontend: детальная страница кампании с таймлайном
- [ ] Frontend: Cart → мультивыбор каналов через корзину

### Спринт 4 — Пополнение баланса (1 неделя)
- [ ] CryptoBotAPI: createInvoice, getBalance, transfer
- [ ] API: POST /api/payments/deposit (создание инвойса)
- [ ] Webhook: POST /api/webhooks/cryptobot (проверка подписи, idempotency)
- [ ] API: POST /api/payments/check (ручная проверка инвойса)
- [ ] Добавление ЮKassa (опционально)
- [ ] Frontend: страница пополнения (выбор метода, сумма, платёжная ссылка)

### Спринт 5 — Вывод средств (1 неделя)
- [ ] Модель WithdrawRequest
- [ ] API: создание заявки, список заявок, отмена
- [ ] Admin: очередь заявок, approve/reject
- [ ] CryptoBot: масс-пеймент (transfer)
- [ ] Комиссия платформы (настраиваемый %)
- [ ] Frontend: страница вывода, история заявок
- [ ] Admin: финансовая сводка

### Спринт 6 — Админ-панель (2 недели)
- [ ] Admin dashboard (KPI: пользователи, каналы, оборот, комиссии)
- [ ] Модерация каналов (очередь + approve/reject)
- [ ] Управление пользователями (бан, смена роли, коррекция баланса)
- [ ] Управление заказами (force-complete, force-cancel)
- [ ] Споры (disputes — просмотр, разрешение, перевод средств)
- [ ] Admin: настройки (комиссия, курсы, лимиты)
- [ ] Bot: админ-команды `/stats`, `/users`, `/channels`
- [ ] Audit log всех админ-действий

### Спринт 7 — Аналитика и бот (1-2 недели)
- [ ] ChannelStats: графики просмотров, подписчиков, ER
- [ ] Кампании: аналитика по дням, стоимость за охват
- [ ] All: история доходов/расходов с графиками
- [ ] Bot: улучшенные уведомления с preview
- [ ] Bot: inline-режим (поиск каналов, баланс)
- [ ] Frontend: recharts для графиков

### Спринт 8 — Production (2 недели)
- [ ] Тесты: pytest + httpx.AsyncClient (все API-ручки)
- [ ] Тесты: bot handlers (aiogram test utils)
- [ ] Тесты: escrow flow (integration)
- [ ] Rate limiting (slowapi)
- [ ] CI/CD: GitHub Actions (lint, typecheck, test, build, deploy)
- [ ] Docker Compose production (API + Bot + PostgreSQL + pg_bouncer)
- [ ] Logging: structlog + Sentry
- [ ] Security audit
- [ ] README, API docs, deployment guide

---

## 8. Примеры кода

### 8.1 Валидация Telegram initData

```python
# app/auth/telegram.py
import hashlib, hmac, json, time
from urllib.parse import parse_qsl, unquote

class InvalidInitDataError(Exception): pass
class ExpiredInitDataError(Exception): pass

def validate_init_data(init_data: str, bot_token: str, expiration: int = 86400) -> dict:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))

    if "hash" not in parsed:
        raise InvalidInitDataError("Missing hash")
    if "auth_date" not in parsed:
        raise InvalidInitDataError("Missing auth_date")

    auth_date = int(parsed["auth_date"])
    now = time.time()
    if now - auth_date > expiration:
        raise ExpiredInitDataError(f"Expired: {int(now - auth_date)}s > {expiration}s")
    if auth_date > now + 30:
        raise InvalidInitDataError("Future auth_date")

    hash_value = parsed.pop("hash")
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, hash_value):
        raise InvalidInitDataError("Hash mismatch")

    if "user" in parsed:
        parsed["user"] = json.loads(unquote(parsed["user"]))

    return parsed
```

```python
# app/auth/deps.py
from fastapi import Header, Depends, HTTPException, status
from sqlalchemy import select
from app.auth.telegram import validate_init_data
from app.db.session import get_session
from app.db.models import User
from app.config import settings

async def get_current_user(
    authorization: str = Header(alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_session),
) -> User:
    try:
        data = validate_init_data(authorization, settings.BOT_TOKEN)
    except (InvalidInitDataError, ExpiredInitDataError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    tg_user = data["user"]
    result = await db.execute(select(User).where(User.id == tg_user["id"]))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            id=tg_user["id"],
            username=tg_user.get("username"),
            first_name=tg_user.get("first_name"),
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

    return user
```

### 8.2 Escrow-сервис

```python
# app/orders/service.py
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import CampaignChannel, User, Transaction

class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_and_hold(self, advertiser_id: int, channel_id: int,
                               amount: Decimal, campaign_id: int) -> CampaignChannel:
        advertiser = await self.db.execute(
            select(User).where(User.id == advertiser_id).with_for_update()
        )
        advertiser = advertiser.scalar_one()

        if advertiser.balance < amount:
            raise InsufficientBalanceError

        # Hold funds
        advertiser.balance -= amount
        advertiser.hold_balance += amount

        cc = CampaignChannel(
            campaign_id=campaign_id, channel_id=channel_id,
            price=amount, status="pending",
            owner_response_deadline=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        self.db.add(cc)
        self.db.add(Transaction(user_id=advertiser_id, amount=-amount,
                                 type="hold", balance_before=..., balance_after=...))
        return cc

    async def release_to_owner(self, cc_id: int) -> CampaignChannel:
        cc = await self.db.execute(
            select(CampaignChannel).where(CampaignChannel.id == cc_id).with_for_update()
        )
        cc = cc.scalar_one()

        campaign = await self.db.get(Campaign, cc.campaign_id)
        advertiser = await self.db.execute(
            select(User).where(User.id == campaign.advertiser_id).with_for_update()
        )
        advertiser = advertiser.scalar_one()

        channel = await self.db.get(Channel, cc.channel_id)
        owner = await self.db.execute(
            select(User).where(User.id == channel.owner_id).with_for_update()
        )
        owner = owner.scalar_one()

        # Release: advertiser hold → owner balance (minus commission)
        commission = (cc.price * Decimal("0.1")).quantize(Decimal("0.01"))
        owner_amount = cc.price - commission

        advertiser.hold_balance -= cc.price
        owner.balance += owner_amount
        # platform fee (e.g., admin user #1)
        platform = await self.db.get(User, 1)
        platform.balance += commission

        cc.status = "completed"
        cc.confirmed_at = datetime.now(timezone.utc)
        return cc
```

### 8.3 CryptoBot интеграция

```python
# app/payments/cryptobot.py
import hashlib, hmac, time
from decimal import Decimal
import aiohttp

class CryptoBotAPI:
    def __init__(self, api_key: str, base_url: str = "https://pay.crypt.bot/api"):
        self._api_key = api_key
        self._base_url = base_url
        self._session: aiohttp.ClientSession | None = None

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        session = self._session or aiohttp.ClientSession()
        headers = {"Crypto-Pay-API-Token": self._api_key, "Content-Type": "application/json"}
        async with session.request(method, f"{self._base_url}/{path}",
                                    headers=headers, **kwargs) as resp:
            body = await resp.json()
            if not body.get("ok"):
                raise CryptoBotError(body.get("error", {}).get("message", "Unknown"))
            return body["result"]

    async def create_invoice(self, amount: Decimal, asset: str = "USDT",
                              payload: str | None = None) -> dict:
        body = {"amount": str(amount), "asset": asset}
        if payload: body["payload"] = payload
        return await self._request("POST", "createInvoice", json=body)

    async def transfer(self, user_id: int, amount: Decimal, asset: str = "USDT",
                        spend_id: str | None = None) -> dict:
        body = {
            "user_id": user_id, "amount": str(amount), "asset": asset,
            "spend_id": spend_id or f"tgad_{int(time.time())}_{user_id}",
        }
        return await self._request("POST", "transfer", json=body)

    @staticmethod
    def verify_webhook(body: bytes, signature: str, api_key: str) -> bool:
        expected = hmac.new(api_key.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
```

### 8.4 Bot handler — уведомление о заказе + inline кнопки

```python
# app/bot/handlers.py
from aiogram import Router, F, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

router = Router()

def order_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"order:approve:{order_id}"),
         InlineKeyboardButton(text="❌ Отклонить", callback_data=f"order:reject:{order_id}")]
    ])

@router.callback_query(F.data.startswith("order:"))
async def handle_order(callback: CallbackQuery, bot: Bot):
    _, action, order_id = callback.data.split(":")
    async with async_session() as session:
        async with session.begin():
            service = OrderService(session)
            if action == "approve":
                order = await service.approve_order(int(order_id))
                await callback.answer("Заказ принят!")
                # notify advertiser
            elif action == "reject":
                order = await service.reject_order(int(order_id))
                await callback.answer("Заказ отклонён")
```

---

## 9. Наводящие вопросы

1. **Гео-таргетинг**: нужен ли фильтр каналов по гео (страна/город) рекламодателем и указание гео аудитории владельцем?

2. **Ценообразование**: только фиксированная цена за пост или также аукцион ( bidding) / CPM / CPC?

3. **ЮKassa / ААIO**: нужно подключать дополнительные российские платёжные системы, или достаточно CryptoBot (USDT → RUB)?

4. **Арбитраж**: какой процесс разрешения споров? Автоматический (если пост не вышел — рефанд) или ручной (админ проверяет)?

5. **Медиа-файлы**: посты могут содержать фото/видео. Нужно S3-хранилище или достаточно ссылок на уже загруженные в Telegram файлы?

6. **Масштабирование**: планируемое количество пользователей и каналов? Нужна ли пагинация с портала (offset/limit) или cursor-based?

7. **Вывод средств**: только CryptoBot (P2P USDT на кошелёк) или также на карты РФ (через ЮKassa mass payouts)?

8. **Язык**: только русский или требуется мультиязычность (i18n)?

9. **Деплой**: где планируется хостинг бэкенда? VPS (Linux), Railway, Fly.io или другое?

10. **Юридическое**: кто является оператором расчётов? Нужна ли комиссия платформы с каждой сделки (и какой %) и как это документируется?
