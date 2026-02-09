import logging
from datetime import date
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from fastapi import Depends

from app.services.storage import (
    save_upload_file,
    save_avatar,
    save_question_image,
    delete_file_by_url,
    SUBDIR_PDFS,
)
from app.services.llm import analyze_question_image
from app.routers.files import require_auth
from app.deps import get_current_user_id, require_subject_owner
from app.services.pdf_parse import extract_text_by_page, parse_page_to_question
from app.models import Question, ImportBatch, User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """上传题目图片，保存到 questions/ 并压缩，占用用户存储配额，返回 /files/questions/..."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")
    path, size = save_question_image(content, file.filename or "image.jpg")
    r = await db.execute(select(User).where(User.id == user_id))
    u = r.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="用户不存在")
    if (u.storage_used_bytes or 0) + size > (u.storage_limit_bytes or 0):
        delete_file_by_url(path)
        raise HTTPException(
            status_code=403,
            detail=f"存储空间不足（已用 {(u.storage_used_bytes or 0) // (1024*1024)}MB / 上限 {(u.storage_limit_bytes or 0) // (1024*1024)}MB），请购买扩容",
        )
    u.storage_used_bytes = (u.storage_used_bytes or 0) + size
    await db.flush()
    return {"url": path}


@router.post("/image/analyze")
async def upload_and_analyze(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """上传错题图片并分析（Coze 工作流优先，否则 OpenAI），占用用户存储配额，返回图片 URL 与题目/解析/答案。"""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")

    filename = file.filename or "image.jpg"
    content_type = file.content_type or ""
    logger.info("[upload/image/analyze] 收到图片: filename=%s, size=%d bytes", filename, len(content))

    path, file_size = save_question_image(content, filename)
    r = await db.execute(select(User).where(User.id == user_id))
    u = r.scalar_one_or_none()
    if not u:
        delete_file_by_url(path)
        raise HTTPException(status_code=401, detail="用户不存在")
    if (u.storage_used_bytes or 0) + file_size > (u.storage_limit_bytes or 0):
        delete_file_by_url(path)
        raise HTTPException(
            status_code=403,
            detail=f"存储空间不足（已用 {(u.storage_used_bytes or 0) // (1024*1024)}MB / 上限 {(u.storage_limit_bytes or 0) // (1024*1024)}MB），请购买扩容",
        )
    u.storage_used_bytes = (u.storage_used_bytes or 0) + file_size
    await db.flush()

    result = await analyze_question_image(image_bytes=content)
    response = {
        "url": path,
        "content": result["content"],
        "analysis": result["analysis"],
        "answer": result["answer"],
    }

    # 打印返回给前端的数据摘要
    logger.info(
        "[upload/image/analyze] 返回前端: url=%s, content_len=%d, analysis_len=%d, answer=%s",
        response["url"], len(response["content"]), len(response["analysis"]), response["answer"][:50] if response["answer"] else ""
    )
    answer_preview = response["answer"][:80] + "..." if len(response["answer"]) > 80 else response["answer"]
    print(f"[upload/image/analyze] 返回前端: url={response['url']}, content_len={len(response['content'])}, analysis_len={len(response['analysis'])}, answer={answer_preview!r}")
    print(f"[upload/image/analyze] 返回完整数据: {response}")

    return response


@router.post("/pdf/import")
async def import_pdf(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    file: UploadFile = File(...),
    subject_id: int = Form(...),
    chapter_id: int | None = Form(None),
):
    """上传 PDF，按页解析为错题并写入指定科目/章节（仅限本人科目）。"""
    if subject_id is None:
        raise HTTPException(status_code=400, detail="缺少 subject_id")
    await require_subject_owner(subject_id, user_id, db)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")
    file_size = len(content)
    r = await db.execute(select(User).where(User.id == user_id))
    u = r.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="用户不存在")
    if (u.storage_used_bytes or 0) + file_size > (u.storage_limit_bytes or 0):
        raise HTTPException(
            status_code=403,
            detail=f"存储空间不足（已用 {(u.storage_used_bytes or 0) // (1024*1024)}MB / 上限 {(u.storage_limit_bytes or 0) // (1024*1024)}MB），请购买扩容",
        )
    path, _ = save_upload_file(content, file.filename or "import.pdf", SUBDIR_PDFS)
    u.storage_used_bytes = (u.storage_used_bytes or 0) + file_size
    await db.flush()
    batch = ImportBatch(subject_id=subject_id, chapter_id=chapter_id, file_url=path)
    db.add(batch)
    await db.flush()
    await db.refresh(batch)
    pages = extract_text_by_page(content)
    today = date.today()
    created = 0
    for page_text in pages:
        if not page_text.strip():
            continue
        parsed = await parse_page_to_question(page_text)
        if not (parsed.get("content") or "").strip() or parsed.get("content") == "(空白页)":
            continue
        q = Question(
            subject_id=subject_id,
            chapter_id=chapter_id,
            content=parsed["content"],
            analysis=parsed.get("analysis") or None,
            answer=parsed.get("answer") or None,
            source="pdf",
            import_batch_id=batch.id,
            next_review_at=today,
            review_stage=0,
            interval_days=1,
        )
        db.add(q)
        created += 1
    await db.flush()
    return {"ok": True, "import_batch_id": batch.id, "pages": len(pages), "created": created}


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(require_auth),
):
    """上传用户头像，保存到 avatars/ 并压缩，占用用户存储配额；若已有本地头像会先释放再计入，返回 /files/avatars/..."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")
    r = await db.execute(select(User).where(User.id == user_id))
    u = r.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="用户不存在")
    old_avatar_url = (u.avatar_url or "").strip()
    if old_avatar_url and old_avatar_url.startswith("/files/avatars/"):
        deleted, freed = delete_file_by_url(old_avatar_url)
        if deleted and freed:
            u.storage_used_bytes = max(0, (u.storage_used_bytes or 0) - freed)
            await db.flush()
    path, size = save_avatar(content, file.filename or "avatar.jpg")
    if (u.storage_used_bytes or 0) + size > (u.storage_limit_bytes or 0):
        delete_file_by_url(path)
        raise HTTPException(
            status_code=403,
            detail=f"存储空间不足（已用 {(u.storage_used_bytes or 0) // (1024*1024)}MB / 上限 {(u.storage_limit_bytes or 0) // (1024*1024)}MB），请购买扩容",
        )
    u.storage_used_bytes = (u.storage_used_bytes or 0) + size
    u.avatar_url = path
    await db.flush()
    return {"url": path}
