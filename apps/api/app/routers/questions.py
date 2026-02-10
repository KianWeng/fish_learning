from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.deps import get_current_user_id, require_subject_owner, require_subject_owner_for_update
from app.models import Question, Chapter, Subject
from app.schemas.question import QuestionCreate, QuestionResponse, QuestionUpdate
from app.services.storage import delete_file_by_url

router = APIRouter()


@router.get("", response_model=list[dict])
async def list_questions(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    subject_id: int | None = None,
    chapter_id: int | None = None,
):
    q = select(Question).join(Subject, Question.subject_id == Subject.id).where(Subject.user_id == user_id)
    if subject_id is not None:
        await require_subject_owner(subject_id, user_id, db)
        q = q.where(Question.subject_id == subject_id)
    if chapter_id is not None:
        r = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
        c = r.scalar_one_or_none()
        if not c:
            raise HTTPException(status_code=404, detail="章节不存在")
        await require_subject_owner(c.subject_id, user_id, db)
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
async def get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    r = await db.execute(select(Question).where(Question.id == question_id))
    x = r.scalar_one_or_none()
    if not x:
        raise HTTPException(status_code=404, detail="错题不存在")
    await require_subject_owner(x.subject_id, user_id, db)
    return x


@router.patch("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    body: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    r = await db.execute(select(Question).where(Question.id == question_id))
    x = r.scalar_one_or_none()
    if not x:
        raise HTTPException(status_code=404, detail="错题不存在")
    await require_subject_owner(x.subject_id, user_id, db)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(x, key, value)
    await db.flush()
    await db.refresh(x)
    return x


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    r = await db.execute(select(Question).where(Question.id == question_id))
    x = r.scalar_one_or_none()
    if not x:
        raise HTTPException(status_code=404, detail="错题不存在")
    await require_subject_owner(x.subject_id, user_id, db)
    image_url_to_del = x.image_url
    analysis_image_url_to_del = getattr(x, "analysis_image_url", None) or None
    await db.delete(x)
    await db.flush()
    total_freed = 0
    for url in (image_url_to_del, analysis_image_url_to_del):
        if url:
            deleted, freed = delete_file_by_url(url)
            if deleted and freed:
                total_freed += freed
    if total_freed > 0:
        from app.models import User
        r = await db.execute(select(User).where(User.id == user_id))
        u = r.scalar_one_or_none()
        if u:
            u.storage_used_bytes = max(0, (u.storage_used_bytes or 0) - total_freed)
            await db.flush()
    return {"ok": True}


@router.post("", response_model=QuestionResponse)
async def create_question(
    body: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    await require_subject_owner_for_update(body.subject_id, user_id, db)
    today = date.today()
    q = Question(
        subject_id=body.subject_id,
        chapter_id=body.chapter_id,
        content=body.content,
        analysis=body.analysis,
        answer=body.answer,
        image_url=body.image_url,
        summary=body.summary,
        analysis_image_url=body.analysis_image_url,
        source=body.source,
        next_review_at=today,
        review_stage=0,
        interval_days=1,
    )
    db.add(q)
    await db.flush()
    await db.refresh(q)
    return q
