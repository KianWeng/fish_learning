from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.deps import get_current_user_id, require_subject_owner
from app.models import Chapter, Question
from app.schemas.chapter import ChapterCreate, ChapterUpdate, ChapterResponse

router = APIRouter()


@router.get("", response_model=list[ChapterResponse])
async def list_chapters(
    subject_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    await require_subject_owner(subject_id, user_id, db)
    r = await db.execute(
        select(Chapter).where(Chapter.subject_id == subject_id).order_by(Chapter.sort, Chapter.id)
    )
    return list(r.scalars().all())


@router.get("/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    r = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    c = r.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="章节不存在")
    await require_subject_owner(c.subject_id, user_id, db)
    return c


@router.post("", response_model=ChapterResponse)
async def create_chapter(
    body: ChapterCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    await require_subject_owner(body.subject_id, user_id, db)
    c = Chapter(
        subject_id=body.subject_id,
        name=body.name,
        sort=body.sort,
        parent_id=body.parent_id,
    )
    db.add(c)
    await db.flush()
    await db.refresh(c)
    return c


@router.put("/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(
    chapter_id: int,
    body: ChapterUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    r = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    c = r.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="章节不存在")
    await require_subject_owner(c.subject_id, user_id, db)
    if body.name is not None:
        c.name = body.name
    if body.sort is not None:
        c.sort = body.sort
    if body.parent_id is not None:
        c.parent_id = body.parent_id
    await db.flush()
    await db.refresh(c)
    return c


@router.delete("/{chapter_id}")
async def delete_chapter(
    chapter_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    r = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    c = r.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="章节不存在")
    await require_subject_owner(c.subject_id, user_id, db)
    count = await db.execute(select(func.count(Question.id)).where(Question.chapter_id == chapter_id))
    if count.scalar() > 0:
        raise HTTPException(status_code=400, detail="该章节下还有错题，无法删除")
    await db.delete(c)
    return {"ok": True}
