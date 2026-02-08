from datetime import date
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from fastapi import Depends

from app.services.storage import save_upload_file
from app.services.llm import analyze_question_image
from app.services.pdf_parse import extract_text_by_page, parse_page_to_question
from app.models import Question, ImportBatch

router = APIRouter()


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")
    path = save_upload_file(content, file.filename or "image.jpg", "images")
    return {"url": path}


@router.post("/image/analyze")
async def upload_and_analyze(file: UploadFile = File(...)):
    """上传错题图片并分析（Coze 工作流优先，否则 OpenAI），返回图片 URL 与题目/解析/答案。"""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")
    path = save_upload_file(content, file.filename or "image.jpg", "images")
    result = await analyze_question_image(image_bytes=content)
    return {"url": path, "content": result["content"], "analysis": result["analysis"], "answer": result["answer"]}


@router.post("/pdf/import")
async def import_pdf(
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    subject_id: int = Form(...),
    chapter_id: int | None = Form(None),
):
    """上传 PDF，按页解析为错题并写入指定科目/章节。"""
    if subject_id is None:
        raise HTTPException(status_code=400, detail="缺少 subject_id")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")
    path = save_upload_file(content, file.filename or "import.pdf", "pdfs")
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
