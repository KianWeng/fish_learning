from datetime import date, datetime
from pydantic import BaseModel


class QuestionCreate(BaseModel):
    subject_id: int
    chapter_id: int | None = None
    content: str
    analysis: str | None = None
    answer: str | None = None
    image_url: str | None = None
    summary: str | None = None
    analysis_image_url: str | None = None
    source: str = "photo"


class QuestionUpdate(BaseModel):
    user_notes: str | None = None
    analysis: str | None = None
    answer: str | None = None
    analysis_image_url: str | None = None


class QuestionResponse(BaseModel):
    id: int
    subject_id: int
    chapter_id: int | None
    content: str
    analysis: str | None
    answer: str | None
    image_url: str | None
    summary: str | None
    analysis_image_url: str | None
    source: str
    next_review_at: date | None
    review_stage: int
    interval_days: int
    user_notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True
