from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users_2db"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    user_name: Mapped[str | None] = mapped_column(String, nullable=True)
    telegram_username: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    bot_start_datetime: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    daily_answers: Mapped[list["DailyAnswer"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    user_events: Mapped[list["UserEvent"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class DailyAnswer(Base):
    __tablename__ = "daily_answers_2db"
    __table_args__ = (Index("idx_daily_answers_user_2db", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users_2db.id", ondelete="CASCADE"), nullable=False
    )
    time_of_day: Mapped[str] = mapped_column(String(20), nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="daily_answers")


class UserEvent(Base):
    __tablename__ = "user_events_2db"
    __table_args__ = (
        Index(
            "idx_user_events_reminders_2db",
            "reminder_24h_sent",
            "reminder_48h_sent",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users_2db.id", ondelete="CASCADE"), nullable=False
    )
    event_code: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    reminder_24h_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_48h_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="user_events")
