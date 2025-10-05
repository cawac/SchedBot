from sqlalchemy import Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.sql import func

from models.base import Base
from models.group import Group

class User(Base):
    __tablename__ = "users"

    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    tg_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, unique=True)
    group_id: Mapped[Group] = mapped_column(Integer, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True)

    group = relationship("Group")