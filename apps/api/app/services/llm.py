import base64
import json
import re
from openai import AsyncOpenAI

from app.config import settings

client = AsyncOpenAI(
    api_key=settings.openai_api_key or "sk-dummy",
    base_url=settings.openai_base_url,
)


async def analyze_question_image(image_base64: str) -> dict:
    """
    根据错题图片调用视觉模型，提取题目、解析、答案。
    返回 {"content": str, "analysis": str, "answer": str}
    """
    prompt = """你是一份错题本应用的助手。请根据用户上传的错题图片，完成以下任务：
1. 准确识别并逐字转录题目内容（含题干、选项或小题，保持原有格式）。
2. 给出该题的解析（思路、步骤、易错点等）。
3. 给出正确答案。

请严格按以下 JSON 格式回复，不要包含其他说明文字：
{"content":"题目全文","analysis":"解析内容","answer":"答案"}
"""
    if not settings.openai_api_key:
        return {
            "content": "[未配置大模型] 请配置 OPENAI_API_KEY 后重试。",
            "analysis": "",
            "answer": "",
        }
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                        },
                    ],
                }
            ],
            max_tokens=2048,
        )
        text = (resp.choices[0].message.content or "").strip()
        # 尝试从回复中解析 JSON
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            data = json.loads(m.group())
            return {
                "content": data.get("content", ""),
                "analysis": data.get("analysis", ""),
                "answer": data.get("answer", ""),
            }
        return {"content": text, "analysis": "", "answer": ""}
    except Exception as e:
        return {
            "content": f"[分析失败] {str(e)}",
            "analysis": "",
            "answer": "",
        }
