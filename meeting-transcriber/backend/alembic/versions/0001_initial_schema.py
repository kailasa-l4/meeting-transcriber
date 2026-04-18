"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.UniqueConstraint("username"),
        sa.CheckConstraint(
            "status IN ('pending','approved','revoked','deleted')",
            name="users_status_check",
        ),
    )

    op.create_table(
        "meetings",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("channel_id", sa.String(), nullable=True),
        sa.Column("slack_thread_ts", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default="recording"),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("session_id"),
    )

    op.create_table(
        "transcripts",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("speaker", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"]),
    )

    op.create_table(
        "summaries",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("time_range", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"]),
    )

    op.create_table(
        "transcriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), server_default="processing"),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("segments", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )


def downgrade() -> None:
    op.drop_table("transcriptions")
    op.drop_table("summaries")
    op.drop_table("transcripts")
    op.drop_table("meetings")
    op.drop_table("users")
