"""
Coze 工作流：鉴权（PAT）、上传图片、调用工作流并解析 JSON 输出。
"""
import json
import logging
import re
import httpx

from app.config import settings

logger = logging.getLogger(__name__)
COZE_UPLOAD_URL = "/v1/files/upload"
COZE_WORKFLOW_RUN_URL = "/v1/workflow/run"


def _get_workflow_timeout() -> float:
    """识图工作流超时（秒），从配置读取，便于 .env 调大。"""
    return float(getattr(settings, "coze_workflow_timeout", 120) or 120)


def _log_timeout_detail(
    e: Exception,
    *,
    filename: str = "",
    file_size: int = 0,
    file_id: str = "",
) -> None:
    """超时时打印详细诊断信息便于排查（含 file_id 便于区分并发请求）。"""
    exc_type = type(e).__name__
    exc_msg = str(e) if str(e) else repr(e)
    req = getattr(e, "request", None)
    req_url = str(getattr(req, "url", None)) if req else ""
    req_method = getattr(req, "method", None) if req else ""
    if not req_url:
        req_url = f"{settings.coze_base_url.rstrip('/')}{COZE_WORKFLOW_RUN_URL}"
    timeout = _get_workflow_timeout()
    lines = [
        "[Coze 超时] ========== 诊断信息 ==========",
        f"  异常类型: {exc_type}",
        f"  异常信息: {exc_msg}",
        f"  当前配置超时: {timeout}s",
        f"  请求 URL: {req_url}",
        f"  请求方法: {req_method or 'POST'}",
        f"  Coze file_id: {file_id or '(未拿到)'}",
        f"  图片文件名: {filename}",
        f"  图片大小: {file_size} bytes ({file_size / 1024:.1f} KB)",
        f"  工作流 ID: {getattr(settings, 'coze_workflow_id', '')}",
        "  若经常超时可在 .env 设置 COZE_WORKFLOW_TIMEOUT=180 或 240",
        "[Coze 超时] =====================================",
    ]
    msg = "\n".join(lines)
    logger.warning("[Coze] 请求超时 file_id=%s size=%d timeout=%s", file_id or "", file_size, timeout)
    print(msg)


async def upload_image_to_coze(file_content: bytes, filename: str = "image.jpg") -> str:
    """
    将图片上传到 Coze，返回 file_id。
    鉴权：Authorization: Bearer {coze_api_key}
    """
    base = settings.coze_base_url.rstrip("/")
    url = base + COZE_UPLOAD_URL
    size = len(file_content)
    logger.info("[Coze] 上传图片: url=%s, filename=%s, size=%d", url, filename, size)
    print(f"[Coze] 上传图片: url={url}, filename={filename}, size={size} bytes")

    headers = {"Authorization": f"Bearer {settings.coze_api_key}"}
    files = {"file": (filename, file_content, "image/jpeg")}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, files=files)
        resp.raise_for_status()
        data = resp.json()

    code = data.get("code")
    msg = data.get("msg", "")
    if code != 0:
        logger.warning("[Coze] 上传失败: code=%s, msg=%s", code, msg)
        print(f"[Coze] 上传失败: code={code}, msg={msg}")
        raise RuntimeError(msg or "Coze 上传失败")

    file_id = data["data"]["id"]
    logger.info("[Coze] 上传成功: file_id=%s", file_id)
    print(f"[Coze] 上传成功: file_id={file_id}")
    return file_id


async def run_workflow(file_id: str) -> str:
    """
    调用 Coze 工作流，传入图片 file_id，返回工作流输出的原始字符串（应为 JSON）。
    """
    base = settings.coze_base_url.rstrip("/")
    url = base + COZE_WORKFLOW_RUN_URL
    param_name = settings.coze_image_parameter or "image"
    body = {
        "workflow_id": settings.coze_workflow_id,
        "parameters": {param_name: {"file_id": file_id}},
    }
    logger.info("[Coze] 调用工作流: url=%s, workflow_id=%s, param=%s, file_id=%s", url, settings.coze_workflow_id, param_name, file_id)
    print(f"[Coze] 调用工作流: url={url}, workflow_id={settings.coze_workflow_id}, param={param_name}, file_id={file_id}")

    headers = {
        "Authorization": f"Bearer {settings.coze_api_key}",
        "Content-Type": "application/json",
    }
    timeout = _get_workflow_timeout()
    logger.info("[Coze] 识图工作流发起请求: file_id=%s, timeout=%ss", file_id, timeout)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()

    code = data.get("code")
    msg = data.get("msg", "")
    if code != 0:
        logger.warning("[Coze] 工作流失败: code=%s, msg=%s", code, msg)
        print(f"[Coze] 工作流失败: code={code}, msg={msg}")
        raise RuntimeError(msg or "Coze 工作流执行失败")

    out = data.get("data")
    if out is None:
        logger.info("[Coze] 工作流返回: data 为空")
        print("[Coze] 工作流返回: data 为空")
        return ""
    if isinstance(out, str):
        logger.info("[Coze] 工作流返回: 字符串, len=%d", len(out))
        print(f"[Coze] 工作流返回: 字符串, len={len(out)}")
        print(f"[Coze] 工作流返回的完整字符串:\n{out}")
        return out
    if isinstance(out, dict):
        keys = list(out.keys())
        logger.info("[Coze] 工作流返回: data.keys=%s", keys)
        print(f"[Coze] 工作流返回: data.keys={keys}")
        if "output" in out:
            v = out["output"]
            raw = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
            print(f"[Coze] 从 data.output 提取, len={len(raw)}")
            print(f"[Coze] 工作流返回的完整字符串:\n{raw}")
            return raw
        if "outputs" in out and isinstance(out["outputs"], list) and len(out["outputs"]) > 0:
            v = out["outputs"][0].get("value") if isinstance(out["outputs"][0], dict) else out["outputs"][0]
            raw = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
            print(f"[Coze] 从 data.outputs[0] 提取, len={len(raw)}")
            print(f"[Coze] 工作流返回的完整字符串:\n{raw}")
            return raw
        if "result" in out:
            v = out["result"]
            raw = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
            print(f"[Coze] 从 data.result 提取, len={len(raw)}")
            print(f"[Coze] 工作流返回的完整字符串:\n{raw}")
            return raw
    raw = json.dumps(out, ensure_ascii=False)
    print(f"[Coze] 整个 data 序列化, len={len(raw)}")
    print(f"[Coze] 工作流返回的完整字符串:\n{raw}")
    return raw


def parse_workflow_json_output(raw: str) -> dict:
    """
    从工作流输出的字符串中解析 JSON，得到 content / analysis / answer。
    支持 Coze 输出格式：problem_content, analysis, answer, options 等。
    """
    logger.info("[Coze] 解析输出: raw_len=%d", len(raw or ""))
    print(f"[Coze] 解析输出: raw_len={len(raw or '')}")

    if not (raw or raw.strip()):
        return {"content": "", "analysis": "", "answer": "", "summary": ""}
    raw = raw.strip()
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        logger.warning("[Coze] 未匹配到 JSON，返回原始前 2000 字")
        print("[Coze] 未匹配到 JSON，返回原始前 2000 字")
        return {"content": raw[:2000], "analysis": "", "answer": "", "summary": ""}
    try:
        obj = json.loads(m.group())
    except json.JSONDecodeError as e:
        logger.warning("[Coze] JSON 解析失败: %s", e)
        print(f"[Coze] JSON 解析失败: {e}")
        return {"content": raw[:2000], "analysis": "", "answer": "", "summary": ""}
    if not isinstance(obj, dict):
        return {"content": raw[:2000], "analysis": "", "answer": "", "summary": ""}

    logger.info("[Coze] 解析到字段: %s", list(obj.keys()))
    print(f"[Coze] 解析到字段: {list(obj.keys())}")

    # 若外层只有 output 且值为 JSON 字符串（工作流常见返回格式），再解析一层
    if isinstance(obj.get("output"), str):
        try:
            inner = json.loads(obj["output"])
            if isinstance(inner, dict):
                obj = inner
                logger.info("[Coze] 解析 output 内层 JSON 成功: %s", list(obj.keys()))
                print(f"[Coze] 解析 output 内层 JSON 成功: {list(obj.keys())}")
        except json.JSONDecodeError as e:
            logger.warning("[Coze] output 内层 JSON 解析失败: %s", e)
            print(f"[Coze] output 内层 JSON 解析失败: {e}")

    content = (
        obj.get("problem_content")
        or obj.get("content")
        or obj.get("题目", "")
    )
    analysis = obj.get("analysis") or obj.get("解析", "")
    answer = obj.get("answer") or obj.get("答案", "")
    summary = obj.get("summary") or ""
    if not summary and ("知识点" in obj or "易错点" in obj):
        parts = []
        if obj.get("知识点"):
            parts.append(f"知识点：{obj['知识点']}")
        if obj.get("易错点"):
            parts.append(f"易错点：{obj['易错点']}")
        if parts:
            summary = "\n".join(parts)

    # 若有 options（如选择题 A/B/C/D/E），追加到题目内容后便于展示
    options = obj.get("options")
    if isinstance(options, dict) and options:
        opts_text = " ".join(f"{k}. {v}" for k, v in sorted(options.items()))
        content = f"{content}\n选项：{opts_text}".strip()

    result = {"content": content, "analysis": analysis, "answer": answer, "summary": summary}
    logger.info("[Coze] 解析结果: content_len=%d, analysis_len=%d, answer=%s, summary_len=%d", len(content), len(analysis), answer[:50] if answer else "", len(summary))
    print(f"[Coze] 解析结果: content_len={len(content)}, analysis_len={len(analysis)}, answer={answer[:80]!r}{'...' if len(answer) > 80 else ''}, summary_len={len(summary)}")
    return result


async def run_report_workflow(stats_input: str) -> str:
    """
    调用学习报告 Coze 工作流，传入 JSON 字符串（见 COZE_REPORT_WORKFLOW.md）。
    返回工作流输出的原始字符串（应为包含 report 与 knowledge_map 的 JSON）。
    """
    base = settings.coze_base_url.rstrip("/")
    url = base + COZE_WORKFLOW_RUN_URL
    param_name = getattr(settings, "coze_report_workflow_parameter", None) or "input"
    body = {
        "workflow_id": settings.coze_report_workflow_id,
        "parameters": {param_name: stats_input},
    }
    # 调试：输入给 Coze 的完整数据
    logger.info("[Coze 报告] 调用报告工作流: workflow_id=%s, param=%s", settings.coze_report_workflow_id, param_name)
    logger.debug("[Coze 报告] 输入 JSON 长度=%d", len(stats_input))
    try:
        input_preview = json.dumps(json.loads(stats_input), ensure_ascii=False, indent=2)[:4000]
    except Exception:
        input_preview = stats_input[:4000]
    print("[Coze 报告] ========== 输入给 Coze 工作流的数据 ==========")
    print(input_preview + ("\n...(截断)" if len(stats_input) > 4000 else ""))
    print("[Coze 报告] =============================================")

    headers = {
        "Authorization": f"Bearer {settings.coze_api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()

    # 调试：Coze 返回的完整响应
    try:
        full_resp = json.dumps(data, ensure_ascii=False, indent=2)
    except Exception:
        full_resp = str(data)
    logger.info("[Coze 报告] 响应 code=%s, msg=%s", data.get("code"), data.get("msg", ""))
    print("[Coze 报告] ========== Coze 返回的完整数据 ==========")
    print(full_resp[:8000] + ("\n...(截断)" if len(full_resp) > 8000 else ""))
    print("[Coze 报告] =============================================")

    code = data.get("code")
    msg = data.get("msg", "")
    if code != 0:
        logger.warning("[Coze] 报告工作流失败: code=%s, msg=%s", code, msg)
        raise RuntimeError(msg or "Coze 报告工作流执行失败")

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


def parse_report_workflow_output(raw: str) -> tuple[str, dict]:
    """
    从报告工作流输出中解析 report（自然语言）与 knowledge_map（思维导图树）。
    返回 (report: str, knowledge_map: dict)。knowledge_map 为 { label, children?, count?, mastered? }。
    """
    if not (raw or raw.strip()):
        return "暂无足够数据生成报告。", {"label": "", "children": []}
    raw = raw.strip()
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        return raw[:2000] if len(raw) > 2000 else raw, {"label": "", "children": []}
    try:
        obj = json.loads(m.group())
    except json.JSONDecodeError:
        return raw[:2000], {"label": "", "children": []}
    if not isinstance(obj, dict):
        return raw[:2000], {"label": "", "children": []}
    # 支持 output 内层
    if isinstance(obj.get("output"), str):
        try:
            inner = json.loads(obj["output"])
            if isinstance(inner, dict):
                obj = inner
        except json.JSONDecodeError:
            pass
    report = obj.get("report") or obj.get("报告") or ""
    knowledge_map = obj.get("knowledge_map") or obj.get("思维导图") or {}
    if not isinstance(knowledge_map, dict):
        knowledge_map = {"label": "", "children": []}
    if "label" not in knowledge_map and "children" not in knowledge_map:
        knowledge_map = {"label": str(knowledge_map)[:100], "children": []}
    return report, knowledge_map


async def analyze_question_image_via_coze(file_content: bytes, filename: str = "image.jpg") -> dict:
    """
    通过 Coze 工作流分析错题图片：上传图片 -> 运行工作流 -> 解析 JSON 输出。
    返回 {"content": str, "analysis": str, "answer": str}
    """
    logger.info("[Coze] analyze_question_image_via_coze 开始: filename=%s, size=%d", filename, len(file_content))
    print(f"[Coze] analyze_question_image_via_coze 开始: filename={filename}, size={len(file_content)} bytes")

    if not settings.coze_api_key or not settings.coze_workflow_id:
        print("[Coze] 未配置 COZE_API_KEY 或 COZE_WORKFLOW_ID，跳过")
        return {
            "content": "[未配置 Coze] 请设置 COZE_API_KEY 与 COZE_WORKFLOW_ID。",
            "analysis": "",
            "answer": "",
            "summary": "",
        }
    try:
        file_id = await upload_image_to_coze(file_content, filename)
        raw_output = await run_workflow(file_id)
        result = parse_workflow_json_output(raw_output)
        print("[Coze] analyze_question_image_via_coze 完成")
        return result
    except httpx.HTTPStatusError as e:
        logger.exception("[Coze] HTTP 错误")
        print(f"[Coze] HTTP 错误: status={e.response.status_code}, body={e.response.text[:200]}")
        return {
            "content": f"[Coze 请求失败] HTTP {e.response.status_code}",
            "analysis": "",
            "answer": "",
            "summary": "",
        }
    except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.WriteTimeout) as e:
        _log_timeout_detail(e, filename=filename, file_size=len(file_content), file_id=file_id)
        return {
            "content": "识图服务响应超时，请稍后重试或换一张更清晰的图片。",
            "analysis": "",
            "answer": "",
            "summary": "",
        }
    except Exception as e:
        logger.exception("[Coze] 分析异常")
        print(f"[Coze] 分析异常: {type(e).__name__}: {e}")
        return {
            "content": f"[Coze 分析失败] {str(e)}",
            "analysis": "",
            "answer": "",
            "summary": "",
        }
