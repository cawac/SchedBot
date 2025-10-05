from sqlalchemy import Text
from sqlalchemy.orm import mapped_column, Mapped, relationship

from models.base import Base


class Group(Base):
    __tablename__ = "groups"

    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    lessons = relationship("LessonGroup", back_populates="group")