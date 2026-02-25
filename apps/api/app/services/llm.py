"""
错题图片分析：优先使用 Coze 工作流，失败时回退到豆包 Doubao（火山方舟 Ark）或 OpenAI。
"""
import base64
import json
import logging
import re
from pathlib import Path

import httpx
from app.config import settings

logger = logging.getLogger(__name__)
_openai_client = None


def _use_ark() -> bool:
    return bool(getattr(settings, "ark_api_key", None))


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


def _is_coze_error_result(result: dict) -> bool:
    """Coze 返回的是否为错误（超时、请求失败等），用于决定是否回退豆包/OpenAI。"""
    content = (result.get("content") or "").strip()
    if not content:
        return True
    if content.startswith("["):
        return True
    for phrase in ("识图服务响应超时", "请求失败", "分析失败", "[未配置", "[Coze"):
        if phrase in content:
            return True
    return False


def _get_question_system_prompt() -> str:
    """识图回退 DeepSeek/OpenAI 时使用的系统 prompt；优先从文件读取。"""
    path = getattr(settings, "openai_question_system_prompt_file", None) or ""
    if path:
        p = Path(path)
        if not p.is_absolute():
            # 相对路径基于 apps/api 目录
            base = Path(__file__).resolve().parent.parent.parent
            p = base / path
        if p.is_file():
            return p.read_text(encoding="utf-8").strip()
    return (getattr(settings, "openai_question_system_prompt", None) or "").strip()


async def analyze_question_image(image_base64: str = "", image_bytes: bytes | None = None) -> dict:
    """
    根据错题图片分析出题目、解析、答案。
    优先走 Coze 工作流；失败则回退到 DeepSeek/OpenAI（需配置 OPENAI_API_KEY）。
    返回 {"content": str, "analysis": str, "answer": str, "summary": str}
    """
    if _use_coze() and image_bytes:
        from app.services.coze_workflow import analyze_question_image_via_coze
        coze_result = await analyze_question_image_via_coze(image_bytes, "image.jpg")
        if _is_coze_error_result(coze_result):
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            if _use_ark():
                logger.info("[识图] Coze 失败，回退到豆包 Doubao (Ark)")
                print("[识图] Coze 失败，回退到豆包 Doubao (Ark)")
                return await _analyze_via_ark(image_b64)
            if settings.openai_api_key:
                logger.info("[识图] Coze 失败，回退到 OpenAI")
                print("[识图] Coze 失败，回退到 OpenAI")
                return await _analyze_via_openai(image_b64)
            logger.warning("[识图] Coze 失败但未配置 ARK_API_KEY 或 OPENAI_API_KEY，无法回退")
            print("[识图] Coze 失败但未配置 ARK_API_KEY 或 OPENAI_API_KEY，无法回退")
        return coze_result

    if image_bytes and not image_base64:
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    if not image_base64 and not _use_ark() and not settings.openai_api_key:
        return {
            "content": "[未配置] 请配置 Coze（COZE_*）或 豆包（ARK_API_KEY）或 OpenAI（OPENAI_API_KEY）后重试。",
            "analysis": "",
            "answer": "",
            "summary": "",
        }
    if _use_ark():
        return await _analyze_via_ark(image_base64)
    return await _analyze_via_openai(image_base64)


async def _analyze_via_ark(image_base64: str) -> dict:
    """使用火山方舟 Ark（豆包 Doubao seed 1.8）Responses API 识图。input 格式：input_image + input_text。"""
    system_prompt = _get_question_system_prompt()
    user_instruction = "请分析这张错题图片，严格按系统提示中的要求只输出一个标准 JSON 对象，无任何其他内容。"
    if system_prompt:
        text_content = f"{system_prompt}\n\n{user_instruction}"
    else:
        text_content = user_instruction

    api_key = getattr(settings, "ark_api_key", None) or ""
    base_url = (getattr(settings, "ark_base_url", None) or "").rstrip("/")
    model = getattr(settings, "ark_vision_model", None) or "doubao-seed-1-8-251228"
    if not api_key or not base_url:
        return {
            "content": "[未配置] 请配置 ARK_API_KEY 与 ARK_BASE_URL。",
            "analysis": "",
            "answer": "",
            "summary": "",
        }
    url = f"{base_url}/responses"
    body = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_base64}"},
                    {"type": "input_text", "text": text_content},
                ],
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        logger.info("[识图 豆包] 发起请求 model=%s url=%s", model, url)
        print(f"[识图 豆包] 发起请求 model={model}")
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
        text = ""
        if isinstance(data, dict):
            output = data.get("output") or data.get("output_text") or data
            if isinstance(output, list) and len(output) > 0:
                first = output[0]
                text = (first.get("text") or first.get("content") or "").strip()
            elif isinstance(output, dict):
                text = (output.get("text") or output.get("output_text") or "").strip()
            if not text and "output" in data and isinstance(data["output"], list):
                for item in data["output"]:
                    if isinstance(item, dict) and (item.get("type") or item.get("role")) == "assistant":
                        text = (item.get("text") or item.get("content") or "").strip()
                        break
        if not text:
            text = json.dumps(data, ensure_ascii=False)[:2000]
        logger.info("[识图 豆包] 原始返回长度=%d", len(text))
        print("[识图 豆包] ========== 原始返回 ==========")
        print(text[:4000] + ("\n...(截断)" if len(text) > 4000 else ""))
        print("[识图 豆包] ================================")
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                obj = json.loads(m.group())
                return _normalize_question_result(obj)
            except json.JSONDecodeError:
                pass
        return {"content": text, "analysis": "", "answer": "", "summary": ""}
    except httpx.HTTPStatusError as e:
        err_body = (e.response.text or "")[:500]
        logger.exception("[识图 豆包] HTTP 错误")
        print(f"[识图 豆包] HTTP 错误: {e.response.status_code} {err_body}")
        return {
            "content": f"[分析失败] HTTP {e.response.status_code} {err_body}",
            "analysis": "",
            "answer": "",
            "summary": "",
        }
    except Exception as e:
        logger.exception("[识图 豆包] 调用异常")
        print(f"[识图 豆包] 调用异常: {type(e).__name__}: {e}")
        return {
            "content": f"[分析失败] {str(e)}",
            "analysis": "",
            "answer": "",
            "summary": "",
        }


def _normalize_question_result(data: dict) -> dict:
    """将模型返回的 JSON 统一为 {content, analysis, answer, summary}。兼容 K12 格式（problem_content、options）与旧格式（content）。"""
    # K12 系统提示词格式：problem_content + options
    content = data.get("problem_content") or data.get("content") or ""
    options = data.get("options")
    if isinstance(options, dict) and options:
        opts_text = "\n".join(f"{k}. {v}" for k, v in sorted(options.items()) if v)
        if opts_text and opts_text not in content:
            content = f"{content.strip()}\n{opts_text}"
    return {
        "content": content,
        "analysis": data.get("analysis", ""),
        "answer": data.get("answer", ""),
        "summary": data.get("summary", ""),
    }


async def _analyze_via_openai(image_base64: str) -> dict:
    system_prompt = _get_question_system_prompt()
    if system_prompt:
        user_prompt = "请分析该错题图片，严格按系统提示中的要求只输出一个标准 JSON 对象，无任何其他内容。"
    else:
        user_prompt = """请根据用户上传的错题图片，完成以下任务：
1. 准确识别并逐字转录题目内容（含题干、选项或小题，保持原有格式）。
2. 给出该题的解析（思路、步骤、易错点等）。
3. 给出正确答案。

请严格按以下 JSON 格式回复，不要包含其他说明文字：
{"content":"题目全文","analysis":"解析内容","answer":"答案","summary":"知识点与易错点简要总结（可选）"}
"""
    if not settings.openai_api_key:
        return {
            "content": "[未配置大模型] 请配置 OPENAI_API_KEY 或 Coze 后重试。",
            "analysis": "",
            "answer": "",
            "summary": "",
        }
    # DeepSeek：content 仅支持 string，用 messages 数组——一条文本、一条图片（data URL 字符串）
    # OpenAI/其他：content 可为数组，单条 user 消息内放 text + image_url
    base_url = (settings.openai_base_url or "").lower()
    is_deepseek = "deepseek" in base_url
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if is_deepseek:
        # 先发图片再发指令，便于模型关联「上面这张图」
        messages.append({"role": "user", "content": f"data:image/jpeg;base64,{image_base64}"})
        messages.append({"role": "user", "content": "请分析上面这张错题图片，严格按系统提示中的要求只输出一个标准 JSON 对象，无任何其他内容。"})
    else:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ],
        })
    model = getattr(settings, "openai_vision_model", None) or "gpt-4o-mini"
    try:
        logger.info("[识图 DeepSeek/OpenAI] 发起请求 model=%s base_url=%s", model, getattr(settings, "openai_base_url", ""))
        print(f"[识图 DeepSeek/OpenAI] 发起请求 model={model}")
        client = _get_openai_client()
        resp = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=2048,
        )
        text = (resp.choices[0].message.content or "").strip()
        logger.info("[识图 DeepSeek/OpenAI] 原始返回长度=%d", len(text))
        print("[识图 DeepSeek/OpenAI] ========== 原始返回 ==========")
        print(text[:4000] + ("\n...(截断)" if len(text) > 4000 else ""))
        print("[识图 DeepSeek/OpenAI] ================================")
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            data = json.loads(m.group())
            return _normalize_question_result(data)
        return {"content": text, "analysis": "", "answer": "", "summary": ""}
    except Exception as e:
        logger.exception("[识图 DeepSeek/OpenAI] 调用异常")
        print(f"[识图 DeepSeek/OpenAI] 调用异常: {type(e).__name__}: {e}")
        return {
            "content": f"[分析失败] {str(e)}",
            "analysis": "",
            "answer": "",
            "summary": "",
        }
