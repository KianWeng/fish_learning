"""
单本错题本学习报告：按 subject_id 聚合题目与复习数据，供大模型生成报告与知识点思维导图。
"""
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Question, Subject, Chapter

MASTERED_STAGE = 5


async def aggregate_subject_stats(db: AsyncSession, subject_id: int) -> dict[str, Any] | None:
    """
    聚合指定错题本下的题目与复习数据。
    返回 None 表示错题本不存在或不属于当前用户（调用方已校验归属时可忽略）；
    返回 dict 包含：subject_name, course, overview, by_chapter, chapter_summaries。
    """
    r = await db.execute(
        select(Subject).where(Subject.id == subject_id)
    )
    subject = r.scalar_one_or_none()
    if not subject:
        return None

    today = date.today()
    # 题目列表：id, chapter_id, summary, next_review_at, review_stage
    q = (
        select(Question.id, Question.chapter_id, Question.summary, Question.next_review_at, Question.review_stage)
        .where(Question.subject_id == subject_id)
    )
    rows = (await db.execute(q)).all()

    def _classify(q_next, q_stage):
        if q_next is None:
            return "new"
        if q_next <= today:
            return "due_today"
        if (q_stage or 0) >= MASTERED_STAGE:
            return "mastered"
        return "scheduled"

    total = len(rows)
    overview = {"total": total, "mastered": 0, "due_today": 0, "new": 0, "scheduled": 0}
    by_chapter: dict[int | None, dict[str, Any]] = {}  # chapter_id -> { chapter_name, total, mastered, due_today, new, scheduled, summaries[] }
    chapter_summaries: dict[int | None, list[str]] = {}

    for row in rows:
        qid, ch_id, summary, next_at, stage = row
        kind = _classify(next_at, stage)
        overview[kind] = overview.get(kind, 0) + 1

        if ch_id not in by_chapter:
            by_chapter[ch_id] = {
                "chapter_id": ch_id,
                "chapter_name": None,
                "total": 0,
                "mastered": 0,
                "due_today": 0,
                "new": 0,
                "scheduled": 0,
            }
            chapter_summaries[ch_id] = []
        by_chapter[ch_id][kind] = by_chapter[ch_id].get(kind, 0) + 1
        by_chapter[ch_id]["total"] += 1
        if summary and (summary := str(summary).strip()):
            chapter_summaries[ch_id].append(summary[:200])

    # 拉取章节名
    if by_chapter:
        ch_ids = [cid for cid in by_chapter if cid is not None]
        if ch_ids:
            ch_r = await db.execute(select(Chapter.id, Chapter.name).where(Chapter.id.in_(ch_ids)))
            for ch_row in ch_r.all():
                by_chapter[ch_row[0]]["chapter_name"] = ch_row[1]
        if None in by_chapter:
            by_chapter[None]["chapter_name"] = "未分类"

    by_chapter_list = [
        {
            "chapter_id": v["chapter_id"],
            "chapter_name": v["chapter_name"] or "未分类",
            "total": v["total"],
            "mastered": v["mastered"],
            "due_today": v["due_today"],
            "new": v["new"],
            "scheduled": v["scheduled"],
        }
        for v in by_chapter.values()
    ]
    # 每章最多保留 5 条 summary 去重
    summaries_by_chapter = []
    for ch_id, summaries in chapter_summaries.items():
        seen = set()
        unique = []
        for s in summaries:
            if s not in seen and len(unique) < 5:
                seen.add(s)
                unique.append(s)
        ch_name = next((c["chapter_name"] for c in by_chapter_list if c["chapter_id"] == ch_id), "未分类")
        summaries_by_chapter.append({"chapter_id": ch_id, "chapter_name": ch_name, "summaries": unique})

    return {
        "subject_name": subject.name or "错题本",
        "course": subject.course or "",
        "overview": overview,
        "by_chapter": by_chapter_list,
        "chapter_summaries": summaries_by_chapter,
    }
