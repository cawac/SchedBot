from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, Mapped, relationship

from models.base import Base


class Subject(Base):
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
