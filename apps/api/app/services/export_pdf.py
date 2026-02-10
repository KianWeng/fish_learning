"""
按错题本（科目）导出 PDF：包含题目图片、题干、解析、答案、自我剖析。
"""
import io
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, KeepTogether

from app.services.storage import get_file_path, save_upload_file, SUBDIR_PDFS

# 图片在页内最大尺寸，控制单图占比以利一页多题
IMG_MAX_WIDTH = 160 * mm
IMG_MAX_HEIGHT = 120 * mm

# 中文字体：优先 CID，否则用 Helvetica（中文会显示为方框）
def _register_chinese_font():
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        return "STSong-Light"
    except Exception:
        return "Helvetica"


def _safe_text(s: str | None, max_len: int = 8000) -> str:
    if s is None:
        return ""
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", s)
    return (s[:max_len] + "…") if len(s) > max_len else s


def build_subject_pdf(subject_name: str, questions: list[dict], image_base_path: Path | None) -> bytes:
    """
    生成错题本 PDF 的字节内容。
    questions: 每项含 content, analysis, answer, user_notes, image_url, created_at 等。
    image_base_path: 用于解析 image_url 为本地路径时的基础路径（可为 None，则仅当 url 为 /files/questions/xxx 时用 get_file_path）。
    """
    buf = io.BytesIO()
    font_name = _register_chinese_font()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="CustomTitle",
        parent=styles["Heading1"],
        fontName=font_name,
        fontSize=16,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        name="Subtitle",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9,
        textColor=colors.HexColor("#666666"),
        spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        name="CustomHeading",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=11,
        spaceBefore=7,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        name="CustomBody",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9,
        spaceAfter=3,
        leading=12,
    )
    label_style = ParagraphStyle(
        name="Label",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=8,
        textColor=colors.HexColor("#888888"),
        spaceAfter=1,
    )

    def para(text: str, style=body_style):
        # 防止 reportlab 报错：尖括号等需转义
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return Paragraph(text, style)

    story = []
    story.append(para(f"错题本：{_safe_text(subject_name, 200)}", title_style))
    story.append(para(f"共 {len(questions)} 道错题", subtitle_style))
    story.append(Spacer(1, 5 * mm))

    for i, q in enumerate(questions, 1):
        story.append(para(f"第 {i} 题", heading_style))

        image_url = (q.get("image_url") or "").strip()
        if image_url:
            img_path = None
            if image_url.startswith("/files/"):
                img_path = get_file_path(image_url)
            if img_path and img_path.is_file():
                try:
                    from PIL import Image as PILImage
                    with PILImage.open(img_path) as pil_img:
                        iw, ih = pil_img.size
                    if iw > 0 and ih > 0:
                        scale = min(IMG_MAX_WIDTH / iw, IMG_MAX_HEIGHT / ih, 1.0)
                        w, h = iw * scale, ih * scale
                        img = RLImage(str(img_path), width=w, height=h)
                        story.append(KeepTogether([img, Spacer(1, 2 * mm)]))
                except Exception:
                    pass

        content = _safe_text(q.get("content"))
        if content:
            story.append(para("题目", label_style))
            story.append(para(content, body_style))

        analysis = _safe_text(q.get("analysis"))
        if analysis:
            story.append(para("解析", label_style))
            story.append(para(analysis, body_style))

        answer = _safe_text(q.get("answer"))
        if answer:
            story.append(para("答案", label_style))
            story.append(para(answer, body_style))

        user_notes = _safe_text(q.get("user_notes"))
        if user_notes:
            story.append(para("自我剖析", label_style))
            story.append(para(user_notes, body_style))

        story.append(Spacer(1, 4 * mm))

    doc.build(story)
    return buf.getvalue()


def export_subject_to_pdf_file(
    subject_name: str, questions: list[dict], out_filename: str | None, storage_key: str
) -> tuple[str, int]:
    """生成 PDF 并保存到 uploads/<storage_key>/pdfs/，返回 (访问路径, 字节数)。storage_key 由 user_storage_key(openid) 得到。"""
    pdf_bytes = build_subject_pdf(subject_name, questions, None)
    safe_name = re.sub(r"[^\w\u4e00-\u9fff\-]", "_", (subject_name or "错题本")[:50])
    filename = (out_filename or f"{safe_name}.pdf").encode("utf-8", errors="ignore").decode("utf-8")
    if not filename.endswith(".pdf"):
        filename += ".pdf"
    path, size = save_upload_file(pdf_bytes, filename, SUBDIR_PDFS, storage_key)
    return path, size
