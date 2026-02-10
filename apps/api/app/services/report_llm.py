"""
学习报告大模型生成：优先 Coze 工作流，未配置时回退 OpenAI。
输入为单本错题本聚合数据，输出自然语言 report 与思维导图 knowledge_map。
"""
import json
import re

from app.config import settings

from app.services.coze_workflow import run_report_workflow, parse_report_workflow_output

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


def _use_coze_report() -> bool:
    return bool(getattr(settings, "coze_report_workflow_id", None))


def _stats_to_input_json(stats: dict) -> str:
    """聚合数据转为 Coze/OpenAI 的输入 JSON 字符串。"""
    return json.dumps(stats, ensure_ascii=False, indent=0)


async def generate_subject_report(stats: dict) -> tuple[str, dict]:
    """
    根据单本错题本聚合数据生成学习报告与知识点思维导图。
    返回 (report: str, knowledge_map: dict)。
    knowledge_map 为树形：{ "label": str, "children": [...], 可选 "count", "mastered" }。
    """
    subject_name = stats.get("subject_name") or "错题本"
    input_json = _stats_to_input_json(stats)

    if _use_coze_report():
        try:
            raw = await run_report_workflow(input_json)
            report, knowledge_map = parse_report_workflow_output(raw)
            return report or "暂无足够数据生成报告。", _normalize_knowledge_map(knowledge_map, subject_name)
        except Exception as e:
            if settings.openai_api_key:
                return await _generate_via_openai(stats, subject_name, input_json)
            return f"报告生成暂时不可用：{str(e)}。", {"label": subject_name, "children": []}

    return await _generate_via_openai(stats, subject_name, input_json)


def _normalize_knowledge_map(m: dict, default_label: str) -> dict:
    """确保 knowledge_map 有 label 和 children。"""
    if not isinstance(m, dict):
        return {"label": default_label, "children": []}
    label = m.get("label") or default_label
    children = m.get("children")
    if not isinstance(children, list):
        children = []
    else:
        children = [_normalize_knowledge_map(c, "子节点") if isinstance(c, dict) else {"label": str(c), "children": []} for c in children]
    return {"label": label, "children": children, **{k: v for k, v in m.items() if k in ("count", "mastered") and v is not None}}


async def _generate_via_openai(stats: dict, subject_name: str, input_json: str) -> tuple[str, dict]:
    """使用 OpenAI 生成报告与思维导图。"""
    if not settings.openai_api_key:
        return "请配置 OPENAI_API_KEY 或 Coze 报告工作流（COZE_REPORT_WORKFLOW_ID）后重试。", {"label": subject_name, "children": []}

    prompt = f"""你是一位学习教练。请根据下面这份「单本错题本」的统计与复习数据，完成两件事：

1. 写一段简短的自然语言学习报告（2～4 句话）：指出在本错题本中哪些章节/题型容易忘或待加强、整体掌握情况，并给出 1～2 条可操作建议。只基于给定数据，不要编造。若题目很少或数据不足，可直接说「暂无足够数据生成报告，多添加错题并复习后再来查看。」

2. 输出一棵知识点思维导图树（JSON 格式）：根节点 label 为本错题本名称（"{subject_name}"），子节点为章节或知识点，每个节点可含 label、count、mastered、children。仅基于给定数据归纳，不要编造节点。

数据（JSON）：
{input_json}

请严格按以下 JSON 格式回复，不要包含其他说明文字。整个回复必须是单个合法 JSON 对象：
{{"report": "你的自然语言报告正文，纯文本", "knowledge_map": {{"label": "错题本名称", "children": [{{"label": "章节或知识点名", "count": 题目数, "mastered": 已掌握数, "children": []}}]}}}}
"""

    try:
        client = _get_openai_client()
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        text = (resp.choices[0].message.content or "").strip()
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return text[:2000] or "报告生成失败。", {"label": subject_name, "children": []}
        obj = json.loads(m.group())
        report = obj.get("report") or "暂无足够数据生成报告。"
        knowledge_map = obj.get("knowledge_map") or {}
        return report, _normalize_knowledge_map(knowledge_map, subject_name)
    except Exception as e:
        return f"报告生成暂时不可用：{str(e)}。", {"label": subject_name, "children": []}
