"""
Coze 工作流：鉴权（PAT）、上传图片、调用工作流并解析 JSON 输出。
"""
import json
import re
import httpx

from app.config import settings

COZE_UPLOAD_URL = "/v1/files/upload"
COZE_WORKFLOW_RUN_URL = "/v1/workflow/run"


async def upload_image_to_coze(file_content: bytes, filename: str = "image.jpg") -> str:
    """
    将图片上传到 Coze，返回 file_id。
    鉴权：Authorization: Bearer {coze_api_key}
    """
    base = settings.coze_base_url.rstrip("/")
    url = base + COZE_UPLOAD_URL
    headers = {"Authorization": f"Bearer {settings.coze_api_key}"}
    files = {"file": (filename, file_content, "image/jpeg")}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, files=files)
        resp.raise_for_status()
        data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(data.get("msg", "Coze 上传失败"))
    return data["data"]["id"]


async def run_workflow(file_id: str) -> str:
    """
    调用 Coze 工作流，传入图片 file_id，返回工作流输出的原始字符串（应为 JSON）。
    """
    base = settings.coze_base_url.rstrip("/")
    url = base + COZE_WORKFLOW_RUN_URL
    headers = {
        "Authorization": f"Bearer {settings.coze_api_key}",
        "Content-Type": "application/json",
    }
    param_name = settings.coze_image_parameter or "image"
    body = {
        "workflow_id": settings.coze_workflow_id,
        "parameters": {param_name: {"file_id": file_id}},
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(data.get("msg", "Coze 工作流执行失败"))
    # 工作流输出可能在 data / data.data / data.outputs 等
    out = data.get("data")
    if out is None:
        return ""
    if isinstance(out, str):
        return out
    if isinstance(out, dict):
        if "output" in out:
            v = out["output"]
            return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
        if "outputs" in out and isinstance(out["outputs"], list) and len(out["outputs"]) > 0:
            v = out["outputs"][0].get("value") if isinstance(out["outputs"][0], dict) else out["outputs"][0]
            return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
        if "result" in out:
            v = out["result"]
            return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return json.dumps(out, ensure_ascii=False)


def parse_workflow_json_output(raw: str) -> dict:
    """
    从工作流输出的字符串中解析 JSON，得到 content / analysis / answer。
    支持 Coze 输出格式：problem_content, analysis, answer, options 等。
    """
    if not (raw or raw.strip()):
        return {"content": "", "analysis": "", "answer": ""}
    raw = raw.strip()
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return {"content": raw[:2000], "analysis": "", "answer": ""}
    try:
        obj = json.loads(m.group())
    except json.JSONDecodeError:
        return {"content": raw[:2000], "analysis": "", "answer": ""}
    if not isinstance(obj, dict):
        return {"content": raw[:2000], "analysis": "", "answer": ""}

    content = (
        obj.get("problem_content")
        or obj.get("content")
        or obj.get("题目", "")
    )
    analysis = obj.get("analysis") or obj.get("解析", "")
    answer = obj.get("answer") or obj.get("答案", "")

    # 若有 options（如选择题 A/B/C/D/E），追加到题目内容后便于展示
    options = obj.get("options")
    if isinstance(options, dict) and options:
        opts_text = " ".join(f"{k}. {v}" for k, v in sorted(options.items()))
        content = f"{content}\n选项：{opts_text}".strip()

    return {"content": content, "analysis": analysis, "answer": answer}


async def analyze_question_image_via_coze(file_content: bytes, filename: str = "image.jpg") -> dict:
    """
    通过 Coze 工作流分析错题图片：上传图片 -> 运行工作流 -> 解析 JSON 输出。
    返回 {"content": str, "analysis": str, "answer": str}
    """
    if not settings.coze_api_key or not settings.coze_workflow_id:
        return {
            "content": "[未配置 Coze] 请设置 COZE_API_KEY 与 COZE_WORKFLOW_ID。",
            "analysis": "",
            "answer": "",
        }
    try:
        file_id = await upload_image_to_coze(file_content, filename)
        raw_output = await run_workflow(file_id)
        return parse_workflow_json_output(raw_output)
    except httpx.HTTPStatusError as e:
        return {
            "content": f"[Coze 请求失败] HTTP {e.response.status_code}",
            "analysis": "",
            "answer": "",
        }
    except Exception as e:
        return {
            "content": f"[Coze 分析失败] {str(e)}",
            "analysis": "",
            "answer": "",
        }
