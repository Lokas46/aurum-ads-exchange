from decimal import Decimal
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Bot
    bot_token: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8001

    # Database
    database_url: str = "sqlite+aiosqlite:///./ad_exchange.db"

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_pg_url(cls, v: Any) -> str:
        if isinstance(v, str) and v.startswith("postgresql://") and "+" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # URLs
    api_base_url: str = "http://localhost:8001"
    webhook_base_url: str = ""

    # Admins
    admin_ids: list[int] = []

    # Dev
    debug: bool = False

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Any) -> list[int]:
        if isinstance(v, str):
            v = v.strip().strip("[]")
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v if isinstance(v, list) else []

    # CryptoBot
    cryptobot_api_key: str = ""
    cryptobot_api_url: str = "https://pay.crypt.bot/api"
    cryptobot_usdt_rate: float = 90.0

    # Kassy.ai
    kassy_api_key: str = ""
    kassy_api_url: str = "https://api.kassy.ai/v1"

    # Platega
    platega_api_key: str = ""
    platega_api_url: str = "https://api.platega.com/v1"

    # Platform
    commission_rate: float = 0.10
    min_withdraw_amount: float = 100.0
    platform_user_id: int = 1
    order_approval_timeout: int = 86400
    init_data_expiration: int = 86400


settings = Settings()
