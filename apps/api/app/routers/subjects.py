from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.deps import get_current_user_id
from app.models import Subject, Question, User
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse
from app.services.export_pdf import export_subject_to_pdf_file, export_report_to_pdf_file
from app.services.storage import delete_file_by_url, user_storage_key
from app.services.storage_quota import get_effective_storage_limit
from app.services.subject_report import aggregate_subject_stats
from app.services.report_llm import generate_subject_report

router = APIRouter()

# 导出 PDF 每次消耗积分
PDF_EXPORT_POINTS_COST = 100


class ExportPdfResponse(BaseModel):
    url: str
    filename: str


class SubjectReportResponse(BaseModel):
    subject_name: str
    report: str
    knowledge_map: dict
    generated_at: str | None = None


@router.get("", response_model=list[SubjectResponse])
async def list_subjects(
    course: str | None = Query(None, description="按科目筛选，不传则返回全部"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """course 为空则不过滤；否则只返回该科目的错题本。"""
    q = select(Subject).where(Subject.user_id == user_id)
    if course is not None and course != "":
        q = q.where(Subject.course == course)
    q = q.order_by(Subject.sort, Subject.id)
    r = await db.execute(q)
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
    s = Subject(user_id=user_id, name=body.name, course=body.course or None, sort=body.sort, cover_url=body.cover_url)
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
    if body.course is not None:
        s.course = body.course or None
    if body.sort is not None:
        s.sort = body.sort
    if body.cover_url is not None:
        s.cover_url = body.cover_url
    await db.flush()
    await db.refresh(s)
    return s


@router.get("/{subject_id}/report", response_model=SubjectReportResponse)
async def get_subject_report(
    subject_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """获取单本错题本的学习报告（自然语言 + 知识点思维导图）。数据不足时返回提示文案。"""
    from app.deps import require_subject_owner
    from datetime import datetime, timezone
    await require_subject_owner(subject_id, user_id, db)
    stats = await aggregate_subject_stats(db, subject_id)
    if not stats:
        raise HTTPException(status_code=404, detail="科目不存在")
    subject_name = stats["subject_name"]
    total = stats["overview"].get("total") or 0
    if total < 2:
        return SubjectReportResponse(
            subject_name=subject_name,
            report="暂无足够数据生成报告，请在本错题本中添加至少 2 道错题并复习后再查看。",
            knowledge_map={"label": subject_name, "children": []},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
    report, knowledge_map = await generate_subject_report(stats)
    return SubjectReportResponse(
        subject_name=subject_name,
        report=report,
        knowledge_map=knowledge_map,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/{subject_id}/report/export/pdf", response_model=ExportPdfResponse)
async def export_report_pdf(
    subject_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """导出学习报告为 PDF（含报告正文 + 知识点总结），消耗积分与错题本 PDF 一致。"""
    from app.deps import require_subject_owner
    r = await db.execute(select(Subject).where(Subject.id == subject_id, Subject.user_id == user_id))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="科目不存在")
    r = await db.execute(select(User).where(User.id == user_id))
    u = r.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="用户不存在")
    if (u.points or 0) < PDF_EXPORT_POINTS_COST:
        raise HTTPException(
            status_code=402,
            detail=f"积分不足，导出 PDF 需要 {PDF_EXPORT_POINTS_COST} 积分（当前 {u.points or 0} 积分）",
        )
    stats = await aggregate_subject_stats(db, subject_id)
    if not stats or (stats["overview"].get("total") or 0) < 1:
        raise HTTPException(status_code=400, detail="该错题本下暂无题目，无法生成报告")
    report, knowledge_map = await generate_subject_report(stats)
    storage_key = user_storage_key(u.openid)
    limit = await get_effective_storage_limit(db, user_id)
    safe_name = (s.name or "错题本").replace("/", "-").strip()[:50]
    filename = f"学习报告-{safe_name}.pdf"
    url, size = export_report_to_pdf_file(s.name or "错题本", report, knowledge_map, storage_key)
    if (u.storage_used_bytes or 0) + size > limit:
        delete_file_by_url(url)
        raise HTTPException(
            status_code=403,
            detail=f"存储空间不足（已用 {(u.storage_used_bytes or 0) // (1024*1024)}MB / 上限 {limit // (1024*1024)}MB），请先清理或扩容",
        )
    u.storage_used_bytes = (u.storage_used_bytes or 0) + size
    u.points = (u.points or 0) - PDF_EXPORT_POINTS_COST
    await db.flush()
    return ExportPdfResponse(url=url, filename=filename)


@router.post("/{subject_id}/export/pdf", response_model=ExportPdfResponse)
async def export_subject_pdf(
    subject_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """按错题本导出 PDF，包含该科目下全部题目的图片、题干、知识点·易错点、解析（含解析附图）、答案、自我剖析。"""
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
            "summary": getattr(x, "summary", None),
            "analysis_image_url": getattr(x, "analysis_image_url", None),
            "created_at": x.created_at.isoformat() if x.created_at else "",
        }
        for x in rows
    ]
    if not questions:
        raise HTTPException(status_code=400, detail="该错题本下暂无题目，无法导出")
    r = await db.execute(select(User).where(User.id == user_id))
    u = r.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="用户不存在")
    if (u.points or 0) < PDF_EXPORT_POINTS_COST:
        raise HTTPException(
            status_code=402,
            detail=f"积分不足，导出 PDF 需要 {PDF_EXPORT_POINTS_COST} 积分（当前 {u.points or 0} 积分）",
        )
    storage_key = user_storage_key(u.openid)
    limit = await get_effective_storage_limit(db, user_id)
    safe_name = (s.name or "错题本").replace("/", "-").strip()[:50]
    filename = f"错题本-{safe_name}.pdf"
    url, size = export_subject_to_pdf_file(s.name or "错题本", questions, filename, storage_key)
    if (u.storage_used_bytes or 0) + size > limit:
        from app.services.storage import delete_file_by_url
        delete_file_by_url(url)
        raise HTTPException(
            status_code=403,
            detail=f"存储空间不足（已用 {(u.storage_used_bytes or 0) // (1024*1024)}MB / 上限 {limit // (1024*1024)}MB），请先清理或扩容",
        )
    u.storage_used_bytes = (u.storage_used_bytes or 0) + size
    u.points = (u.points or 0) - PDF_EXPORT_POINTS_COST
    await db.flush()
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
    from app.models import User
    cover_url_to_del = s.cover_url
    await db.delete(s)
    await db.flush()
    if cover_url_to_del:
        deleted, freed = delete_file_by_url(cover_url_to_del)
        if deleted and freed and freed > 0:
            r = await db.execute(select(User).where(User.id == user_id))
            u = r.scalar_one_or_none()
            if u:
                u.storage_used_bytes = max(0, (u.storage_used_bytes or 0) - freed)
                await db.flush()
    return {"ok": True}
