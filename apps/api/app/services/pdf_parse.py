"""从 PDF 按页提取文本，并调用大模型解析为题目/解析/答案。"""
import io
import json
import re
from openai import AsyncOpenAI

from app.config import settings

client = AsyncOpenAI(
    api_key=settings.openai_api_key or "sk-dummy",
    base_url=settings.openai_base_url,
)


def extract_text_by_page(pdf_bytes: bytes) -> list[str]:
    """按页提取文本，返回每页文本列表。"""
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for i in range(len(doc)):
        page = doc.load_page(i)
        pages.append(page.get_text().strip())
    doc.close()
    return pages


async def parse_page_to_question(page_text: str) -> dict:
    """将一页文本用大模型解析为题目、解析、答案。"""
    if not page_text.strip():
        return {"content": "(空白页)", "analysis": "", "answer": ""}
    if not settings.openai_api_key:
        return {"content": page_text[:2000], "analysis": "", "answer": ""}
    prompt = """以下是一份错题或习题中的一页内容。请识别其中的题目（可能有多道小题），并给出解析与答案。
请严格按以下 JSON 格式回复，不要包含其他说明：
{"content":"题目全文（可含多题）","analysis":"解析","answer":"答案"}
"""
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt + "\n\n" + page_text[:4000]}],
            max_tokens=2048,
        )
        text = (resp.choices[0].message.content or "").strip()
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            data = json.loads(m.group())
            return {
                "content": data.get("content", ""),
                "analysis": data.get("analysis", ""),
                "answer": data.get("answer", ""),
            }
        return {"content": text[:2000], "analysis": "", "answer": ""}
    except Exception as e:
        return {"content": page_text[:2000] + f"\n[解析失败: {e}]", "analysis": "", "answer": ""}
