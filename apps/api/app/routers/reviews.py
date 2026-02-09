from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.deps import get_current_user_id, require_subject_owner
from app.models import Question, Subject
from app.services.ebbinghaus import next_review_date

router = APIRouter()


class ReviewResultBody(BaseModel):
    rating: str  # remember | vague | forget


@router.get("/today")
async def today_reviews(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    today = date.today()
    r = await db.execute(
        select(Question)
        .join(Subject, Question.subject_id == Subject.id)
        .where(Subject.user_id == user_id, Question.next_review_at <= today)
        .order_by(Question.next_review_at)
    )
    rows = r.scalars().all()
    return [
        {
            "id": q.id,
            "subject_id": q.subject_id,
            "content": q.content,
            "analysis": q.analysis,
            "answer": q.answer,
            "image_url": q.image_url,
            "next_review_at": q.next_review_at.isoformat() if q.next_review_at else None,
        }
        for q in rows
    ]


@router.post("/{question_id}/result")
async def submit_review_result(
    question_id: int,
    body: ReviewResultBody,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    if body.rating not in ("remember", "vague", "forget"):
        raise HTTPException(status_code=400, detail="rating 须为 remember / vague / forget")
    r = await db.execute(select(Question).where(Question.id == question_id))
    q = r.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="错题不存在")
    await require_subject_owner(q.subject_id, user_id, db)
    today = date.today()
    interval = q.interval_days or 1
    stage = q.review_stage or 0
    next_at, new_interval = next_review_date(today, interval, stage, body.rating)
    q.next_review_at = next_at
    q.interval_days = new_interval
    q.review_stage = stage + 1
    await db.flush()
    return {"ok": True, "next_review_at": next_at.isoformat(), "interval_days": new_interval}
