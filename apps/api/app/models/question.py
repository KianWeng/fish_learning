from datetime import date, datetime
from sqlalchemy import String, Integer, ForeignKey, Text, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class QuestionSource(str, enum.Enum):
    photo = "photo"
    pdf = "pdf"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    chapter_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("chapters.id", ondelete="SET NULL"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source: Mapped[str] = mapped_column(String(16), default=QuestionSource.photo.value)
    next_review_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_stage: Mapped[int] = mapped_column(Integer, default=0)
    interval_days: Mapped[int] = mapped_column(Integer, default=1)
    import_batch_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True)
    user_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    subject = relationship("Subject", back_populates="questions")
    chapter = relationship("Chapter", back_populates="questions")
    import_batch = relationship("ImportBatch", back_populates="questions")
