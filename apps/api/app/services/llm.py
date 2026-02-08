"""
错题图片分析：优先使用 Coze 工作流，未配置时回退到 OpenAI 视觉模型。
"""
import base64
import json
import re

from app.config import settings

# 仅当使用 OpenAI 时初始化
_openai_client = None

def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import AsyncOpenAI
        _openai_client = AsyncOpenAI(
            api_key=settings.openai_api_key or "sk-dummy",
            base_url=settings.openai_base_url,
        )
    return _openai_client


def _use_coze() -> bool:
    return bool(settings.coze_api_key and settings.coze_workflow_id)


async def analyze_question_image(image_base64: str = "", image_bytes: bytes | None = None) -> dict:
    """
    根据错题图片分析出题目、解析、答案。
    优先走 Coze 工作流（需配置 COZE_API_KEY、COZE_WORKFLOW_ID）；
    否则使用 OpenAI 视觉接口（需配置 OPENAI_API_KEY）。
    返回 {"content": str, "analysis": str, "answer": str}
    """
    if _use_coze() and image_bytes:
        from app.services.coze_workflow import analyze_question_image_via_coze
        return await analyze_question_image_via_coze(image_bytes, "image.jpg")

    if image_bytes and not image_base64:
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    if not image_base64 and not settings.openai_api_key:
        return {
            "content": "[未配置] 请配置 Coze（COZE_API_KEY、COZE_WORKFLOW_ID）或 OpenAI（OPENAI_API_KEY）后重试。",
            "analysis": "",
            "answer": "",
        }
    return await _analyze_via_openai(image_base64)


async def _analyze_via_openai(image_base64: str) -> dict:
    prompt = """你是一份错题本应用的助手。请根据用户上传的错题图片，完成以下任务：
1. 准确识别并逐字转录题目内容（含题干、选项或小题，保持原有格式）。
2. 给出该题的解析（思路、步骤、易错点等）。
3. 给出正确答案。

请严格按以下 JSON 格式回复，不要包含其他说明文字：
{"content":"题目全文","analysis":"解析内容","answer":"答案"}
"""
    if not settings.openai_api_key:
        return {
            "content": "[未配置大模型] 请配置 OPENAI_API_KEY 或 Coze 后重试。",
            "analysis": "",
            "answer": "",
        }
    try:
        client = _get_openai_client()
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
