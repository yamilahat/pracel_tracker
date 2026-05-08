from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UuidPrimaryKeyMixin


class User(UuidPrimaryKeyMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    oauth_tokens = relationship(
        "OAuthToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    emails = relationship(
        "Email",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    gmail_sync_state = relationship(
        "GmailSyncState",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
