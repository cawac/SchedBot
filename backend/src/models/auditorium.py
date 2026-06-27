from sqlalchemy import Integer, String, Index
from sqlalchemy.orm import mapped_column, Mapped, relationship

from models.base import Base


class Auditorium(Base):
    __tablename__ = "auditoriums"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    number: Mapped[str] = mapped_column(String(20), nullable=True)
    building: Mapped[str] = mapped_column(String(100), nullable=False)
    floor: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=True)
    type: Mapped[str] = mapped_column(String(30), nullable=False, default='CLASSROOM')

    lessons = relationship("Lesson", back_populates="auditorium")

    __table_args__ = (
        Index('ix_auditorium_building_number', 'building', 'number'),
    )
