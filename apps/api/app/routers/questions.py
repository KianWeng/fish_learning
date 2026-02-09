from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Question
from app.schemas.question import QuestionCreate, QuestionResponse

router = APIRouter()


@router.get("", response_model=list[dict])
async def list_questions(
    db: AsyncSession = Depends(get_db),
    subject_id: int | None = None,
    chapter_id: int | None = None,
):
    q = select(Question)
    if subject_id is not None:
        q = q.where(Question.subject_id == subject_id)
    if chapter_id is not None:
        q = q.where(Question.chapter_id == chapter_id)
    q = q.order_by(Question.created_at.desc())
    r = await db.execute(q)
    rows = r.scalars().all()
    return [
        {
            "id": x.id,
            "subject_id": x.subject_id,
            "chapter_id": x.chapter_id,
            "content": (x.content or "")[:100] + ("..." if len(x.content or "") > 100 else ""),
            "created_at": x.created_at.isoformat(),
        }
        for x in rows
    ]


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Question).where(Question.id == question_id))
    x = r.scalar_one_or_none()
    if not x:
        raise HTTPException(status_code=404, detail="错题不存在")
    return x


@router.delete("/{question_id}")
async def delete_question(question_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Question).where(Question.id == question_id))
    x = r.scalar_one_or_none()
    if not x:
        raise HTTPException(status_code=404, detail="错题不存在")
    await db.delete(x)
    await db.flush()
    return {"ok": True}


@router.post("", response_model=QuestionResponse)
async def create_question(body: QuestionCreate, db: AsyncSession = Depends(get_db)):
    today = date.today()
    q = Question(
        subject_id=body.subject_id,
        chapter_id=body.chapter_id,
        content=body.content,
        analysis=body.analysis,
        answer=body.answer,
        image_url=body.image_url,
        source=body.source,
        next_review_at=today,
        review_stage=0,
        interval_days=1,
    )
    db.add(q)
    await db.flush()
    await db.refresh(q)
    return q
