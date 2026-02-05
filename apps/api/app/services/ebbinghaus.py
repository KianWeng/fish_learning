"""艾宾浩斯复习间隔：标准序列 1,2,4,7,15 天，再根据反馈系数调整。"""
from datetime import date, timedelta

# 标准间隔（天）
INTERVALS = [1, 2, 4, 7, 15]

# 用户反馈对应的间隔系数：记得/模糊/忘记
RATING_FACTOR = {"remember": 1.0, "vague": 0.6, "forget": 0.3}


def next_review_date(
    today: date,
    current_interval_days: int,
    review_stage: int,
    rating: str,
) -> tuple[date, int]:
    """
    根据当前间隔、阶段和用户反馈，计算下次复习日期与新的间隔天数。
    返回 (next_review_at, new_interval_days)。
    """
    factor = RATING_FACTOR.get(rating, 0.6)
    if review_stage < len(INTERVALS):
        # 前几轮使用标准序列
        next_interval = INTERVALS[review_stage]
    else:
        next_interval = max(1, int(current_interval_days * factor))
        next_interval = min(next_interval, 60)  # 上限 60 天
    next_date = today + timedelta(days=next_interval)
    return next_date, next_interval
