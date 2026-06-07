"""initial_schema

Revision ID: 8645314055b7
Revises:
Create Date: 2026-06-07 18:13:46.736249
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8645314055b7"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="advertiser"),
        sa.Column("balance_rub", sa.Float(), nullable=False, server_default="0"),
        sa.Column("hold_balance_rub", sa.Float(), nullable=False, server_default="0"),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_onboarded", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "payment_invoices",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("asset", sa.String(20), nullable=False, server_default="USDT"),
        sa.Column("crypto_bot_invoice_id", sa.BigInteger(), nullable=True),
        sa.Column("kassy_payment_id", sa.String(255), nullable=True),
        sa.Column("platega_payment_id", sa.String(255), nullable=True),
        sa.Column("payload", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("pay_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_invoices_user_id"), "payment_invoices", ["user_id"], unique=False)

    op.create_table(
        "withdraw_requests",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("fee", sa.Float(), nullable=False, server_default="0"),
        sa.Column("net_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("asset", sa.String(20), nullable=False, server_default="USDT"),
        sa.Column("destination_type", sa.String(30), nullable=False),
        sa.Column("destination_details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("admin_id", sa.BigInteger(), nullable=True),
        sa.Column("crypto_bot_transfer_id", sa.String(255), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"], ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_withdraw_requests_user_id"), "withdraw_requests", ["user_id"], unique=False)

    op.create_table(
        "channels",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("chat_id", sa.BigInteger(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("invite_link", sa.String(500), nullable=True),
        sa.Column("subscribers_count", sa.Integer(), nullable=True),
        sa.Column("avg_views", sa.Integer(), nullable=True),
        sa.Column("avg_er", sa.Float(), nullable=True),
        sa.Column("categories", sa.String(500), nullable=True),
        sa.Column("price_per_post", sa.Float(), nullable=True),
        sa.Column("price_per_hold", sa.Float(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_moderated", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("moderator_id", sa.BigInteger(), nullable=True),
        sa.Column("moderation_comment", sa.Text(), nullable=True),
        sa.Column("bot_added", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ),
        sa.ForeignKeyConstraint(["moderator_id"], ["users.id"], ),
        sa.UniqueConstraint("chat_id"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_channels_owner_id"), "channels", ["owner_id"], unique=False)

    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("advertiser_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("channel_owner_id", sa.BigInteger(), nullable=True),
        sa.Column("channel_name", sa.String(255), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("commission", sa.Float(), nullable=True),
        sa.Column("commission_rate", sa.Float(), nullable=True),
        sa.Column("owner_amount", sa.Float(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("post_text", sa.Text(), nullable=True),
        sa.Column("post_link", sa.String(500), nullable=True),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["advertiser_id"], ["users.id"], ),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"], ),
        sa.ForeignKeyConstraint(["channel_owner_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_advertiser_id"), "orders", ["advertiser_id"], unique=False)
    op.create_index(op.f("ix_orders_channel_id"), "orders", ["channel_id"], unique=False)

    op.create_table(
        "transactions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("balance_before", sa.Float(), nullable=True),
        sa.Column("balance_after", sa.Float(), nullable=True),
        sa.Column("hold_before", sa.Float(), nullable=True),
        sa.Column("hold_after", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="RUB"),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("payment_system", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_user_id"), "transactions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_transactions_user_id"), table_name="transactions")
    op.drop_table("transactions")
    op.drop_index(op.f("ix_orders_channel_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_advertiser_id"), table_name="orders")
    op.drop_table("orders")
    op.drop_index(op.f("ix_channels_owner_id"), table_name="channels")
    op.drop_table("channels")
    op.drop_index(op.f("ix_withdraw_requests_user_id"), table_name="withdraw_requests")
    op.drop_table("withdraw_requests")
    op.drop_index(op.f("ix_payment_invoices_user_id"), table_name="payment_invoices")
    op.drop_table("payment_invoices")
    op.drop_table("users")
