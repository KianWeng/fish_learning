from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Subject, Question
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse

router = APIRouter()


@router.get("", response_model=list[SubjectResponse])
async def list_subjects(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Subject).order_by(Subject.sort, Subject.id))
    return list(r.scalars().all())


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(subject_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Subject).where(Subject.id == subject_id))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="科目不存在")
    return s


@router.post("", response_model=SubjectResponse)
async def create_subject(body: SubjectCreate, db: AsyncSession = Depends(get_db)):
    s = Subject(name=body.name, sort=body.sort, cover_url=body.cover_url)
    db.add(s)
    await db.flush()
    await db.refresh(s)
    return s


@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(subject_id: int, body: SubjectUpdate, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Subject).where(Subject.id == subject_id))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="科目不存在")
    if body.name is not None:
        s.name = body.name
    if body.sort is not None:
        s.sort = body.sort
    if body.cover_url is not None:
        s.cover_url = body.cover_url
    await db.flush()
    await db.refresh(s)
    return s


@router.delete("/{subject_id}")
async def delete_subject(subject_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Subject).where(Subject.id == subject_id))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="科目不存在")
    count = await db.execute(select(func.count(Question.id)).where(Question.subject_id == subject_id))
    if count.scalar() > 0:
        raise HTTPException(status_code=400, detail="该科目下还有错题，无法删除")
    await db.delete(s)
    return {"ok": True}
