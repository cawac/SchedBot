from sqlalchemy import Integer, ForeignKey, DateTime, String, JSON, Index, Column
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import func
from datetime import datetime

from models.base import Base


class UserAction(Base):
    __tablename__ = "user_actions"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    command_name: Mapped[str] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    action_metadata = Column('metadata', JSON, nullable=True)

    user = relationship("User")

    __table_args__ = (
        Index('ix_user_action_user_id', 'user_id'),
        Index('ix_user_action_timestamp', 'timestamp'),
        Index('ix_user_action_command', 'command_name'),
        Index('ix_user_action_timestamp_user_id', 'timestamp', 'user_id'),
    )
