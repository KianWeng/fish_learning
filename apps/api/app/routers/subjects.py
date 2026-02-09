from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.deps import get_current_user_id
from app.models import Subject, Question
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse
from app.services.export_pdf import export_subject_to_pdf_file

router = APIRouter()


class ExportPdfResponse(BaseModel):
    url: str
    filename: str


@router.get("", response_model=list[SubjectResponse])
async def list_subjects(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    r = await db.execute(
        select(Subject).where(Subject.user_id == user_id).order_by(Subject.sort, Subject.id)
    )
    return list(r.scalars().all())


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    r = await db.execute(select(Subject).where(Subject.id == subject_id, Subject.user_id == user_id))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="科目不存在")
    return s


@router.post("", response_model=SubjectResponse)
async def create_subject(
    body: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    s = Subject(user_id=user_id, name=body.name, sort=body.sort, cover_url=body.cover_url)
    db.add(s)
    await db.flush()
    await db.refresh(s)
    return s


@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: int,
    body: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    r = await db.execute(select(Subject).where(Subject.id == subject_id, Subject.user_id == user_id))
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


@router.post("/{subject_id}/export/pdf", response_model=ExportPdfResponse)
async def export_subject_pdf(
    subject_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """按错题本导出 PDF，包含该科目下全部题目的图片、题干、解析、答案、自我剖析。"""
    r = await db.execute(select(Subject).where(Subject.id == subject_id, Subject.user_id == user_id))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="科目不存在")
    q = (
        select(Question)
        .where(Question.subject_id == subject_id)
        .order_by(Question.chapter_id, Question.created_at.desc())
    )
    rows = (await db.execute(q)).scalars().all()
    questions = [
        {
            "content": x.content or "",
            "analysis": x.analysis,
            "answer": x.answer,
            "user_notes": x.user_notes,
            "image_url": x.image_url,
            "created_at": x.created_at.isoformat() if x.created_at else "",
        }
        for x in rows
    ]
    if not questions:
        raise HTTPException(status_code=400, detail="该错题本下暂无题目，无法导出")
    safe_name = (s.name or "错题本").replace("/", "-").strip()[:50]
    filename = f"错题本-{safe_name}.pdf"
    url = export_subject_to_pdf_file(s.name or "错题本", questions, filename)
    return ExportPdfResponse(url=url, filename=filename)


@router.delete("/{subject_id}")
async def delete_subject(
    subject_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    r = await db.execute(
        select(Subject).where(Subject.id == subject_id, Subject.user_id == user_id).with_for_update()
    )
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="科目不存在")
    count = await db.execute(select(func.count(Question.id)).where(Question.subject_id == subject_id))
    if count.scalar() > 0:
        raise HTTPException(status_code=400, detail="该科目下还有错题，无法删除")
    await db.delete(s)
    return {"ok": True}
