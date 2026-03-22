import logging
from datetime import date
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from fastapi import Depends

from app.services.storage import (
    save_upload_file,
    save_avatar,
    save_avatar_login,
    save_question_image,
    delete_file_by_url,
    user_storage_key,
    list_user_pdfs,
    SUBDIR_PDFS,
)
from app.services.llm import analyze_question_image
from app.routers.files import require_auth
from app.deps import get_current_user_id, require_subject_owner
from app.services.pdf_parse import extract_text_by_page, parse_page_to_question
from app.services.storage_quota import get_effective_storage_limit
from app.models import Question, ImportBatch, User

logger = logging.getLogger(__name__)
router = APIRouter()


# 单次上传最大 2MB，用于登录头像等未鉴权上传
MAX_AVATAR_LOGIN_BYTES = 2 * 1024 * 1024


@router.post("/avatar-login")
async def upload_avatar_login(file: UploadFile = File(...)):
    """登录页上传头像（免鉴权）。保存到 uploads/login/avatars/，返回 /files/avatars/login/xxx。限制 2MB、仅图片。"""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")
    if len(content) > MAX_AVATAR_LOGIN_BYTES:
        raise HTTPException(status_code=400, detail="图片不能超过 2MB")
    ct = (file.content_type or "").lower()
    if not ct.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图片")
    path, _ = save_avatar_login(content, file.filename or "avatar.jpg")
    return {"url": path}


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
    r = await db.execute(select(User).where(User.id == user_id))
    u = r.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="用户不存在")
    storage_key = user_storage_key(u.openid)
    limit = await get_effective_storage_limit(db, user_id)
    path, size = save_question_image(content, file.filename or "image.jpg", storage_key)
    if (u.storage_used_bytes or 0) + size > limit:
        delete_file_by_url(path)
        raise HTTPException(
            status_code=403,
            detail=f"存储空间不足（已用 {(u.storage_used_bytes or 0) // (1024*1024)}MB / 上限 {limit // (1024*1024)}MB），请购买扩容",
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
    """上传错题图片并分析（默认百炼 OpenAI 兼容优先，可配置 Coze 优先），占用用户存储配额，返回图片 URL 与题目/解析/答案。"""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")

    filename = file.filename or "image.jpg"
    content_type = file.content_type or ""
    logger.info("[upload/image/analyze] 收到图片: filename=%s, size=%d bytes", filename, len(content))

    r = await db.execute(select(User).where(User.id == user_id))
    u = r.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="用户不存在")
    storage_key = user_storage_key(u.openid)
    limit = await get_effective_storage_limit(db, user_id)
    path, file_size = save_question_image(content, filename, storage_key)
    if (u.storage_used_bytes or 0) + file_size > limit:
        delete_file_by_url(path)
        raise HTTPException(
            status_code=403,
            detail=f"存储空间不足（已用 {(u.storage_used_bytes or 0) // (1024*1024)}MB / 上限 {limit // (1024*1024)}MB），请购买扩容",
        )
    u.storage_used_bytes = (u.storage_used_bytes or 0) + file_size
    await db.flush()

    try:
        result = await analyze_question_image(image_bytes=content)
    except Exception as e:
        logger.exception("[upload/image/analyze] 识图异常，仍返回 200 带 url 供前端弹「手动输入」")
        err_msg = getattr(e, "message", str(e)) or "识图服务异常，请稍后重试或换一张更清晰的图片。"
        if len(err_msg) > 200:
            err_msg = err_msg[:200] + "…"
        result = {
            "content": err_msg,
            "analysis": "",
            "answer": "",
            "summary": "",
        }

    response = {
        "url": path,
        "content": result["content"],
        "analysis": result.get("analysis", ""),
        "answer": result.get("answer", ""),
        "summary": result.get("summary", ""),
    }

    logger.info(
        "[upload/image/analyze] 返回前端: url=%s, content_len=%d",
        response["url"], len(response["content"]),
    )
    return response


class DeleteImageBody(BaseModel):
    url: str


@router.post("/image/delete")
async def delete_question_image(
    body: DeleteImageBody,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """删除一次上传的题目图片（如识别失败后用户选择不手动输入时调用），仅允许删除本人存储下的 /files/questions/ 文件，并扣减已用容量。"""
    url = (body.url or "").strip()
    if not url.startswith("/files/questions/"):
        raise HTTPException(status_code=400, detail="仅支持删除题目图片")
    r = await db.execute(select(User).where(User.id == user_id))
    u = r.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="用户不存在")
    storage_key = user_storage_key(u.openid)
    if f"/files/questions/{storage_key}/" not in url:
        raise HTTPException(status_code=403, detail="只能删除本人上传的图片")
    deleted, freed = delete_file_by_url(url)
    if not deleted:
        raise HTTPException(status_code=404, detail="文件不存在或已删除")
    u.storage_used_bytes = max(0, (u.storage_used_bytes or 0) - freed)
    await db.flush()
    return {"ok": True}


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
    limit = await get_effective_storage_limit(db, user_id)
    if (u.storage_used_bytes or 0) + file_size > limit:
        raise HTTPException(
            status_code=403,
            detail=f"存储空间不足（已用 {(u.storage_used_bytes or 0) // (1024*1024)}MB / 上限 {limit // (1024*1024)}MB），请购买扩容",
        )
    storage_key = user_storage_key(u.openid)
    path, _ = save_upload_file(content, file.filename or "import.pdf", SUBDIR_PDFS, storage_key)
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


@router.get("/pdfs")
async def list_pdfs(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """列出当前用户所有 PDF（导入与导出的），用于 PDF 管理。返回 [{url, filename, size}, ...]。"""
    r = await db.execute(select(User).where(User.id == user_id))
    u = r.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="用户不存在")
    storage_key = user_storage_key(u.openid)
    return list_user_pdfs(storage_key)


@router.delete("/pdfs/{filename}")
async def delete_pdf(
    filename: str,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """删除当前用户的一个 PDF 文件，并扣减存储用量。filename 为列表接口返回的 filename（如 xxx.pdf）。"""
    filename = filename.strip().lstrip("/")
    if not filename or len(filename) > 64 or not all(c.isalnum() or c in ".-_" for c in filename):
        raise HTTPException(status_code=400, detail="文件名不合法")
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持删除 PDF 文件")
    r = await db.execute(select(User).where(User.id == user_id))
    u = r.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="用户不存在")
    storage_key = user_storage_key(u.openid)
    url = f"/files/{SUBDIR_PDFS}/{storage_key}/{filename}"
    deleted, freed = delete_file_by_url(url)
    if not deleted:
        raise HTTPException(status_code=404, detail="文件不存在或已删除")
    u.storage_used_bytes = max(0, (u.storage_used_bytes or 0) - freed)
    await db.flush()
    return {"ok": True, "freed": freed}


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
    storage_key = user_storage_key(u.openid)
    limit = await get_effective_storage_limit(db, user_id)
    path, size = save_avatar(content, file.filename or "avatar.jpg", storage_key)
    if (u.storage_used_bytes or 0) + size > limit:
        delete_file_by_url(path)
        raise HTTPException(
            status_code=403,
            detail=f"存储空间不足（已用 {(u.storage_used_bytes or 0) // (1024*1024)}MB / 上限 {limit // (1024*1024)}MB），请购买扩容",
        )
    u.storage_used_bytes = (u.storage_used_bytes or 0) + size
    u.avatar_url = path
    await db.flush()
    return {"url": path}
