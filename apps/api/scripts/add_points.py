"""
运维脚本：为指定用户增加或扣减积分。
用法：
  python scripts/add_points.py --user Zephyr --points 10000   # 增加 10000
  python scripts/add_points.py --user 1 --points -5000        # 扣减 5000（负数表示扣减）
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User


def parse_args():
    p = argparse.ArgumentParser(description="为指定用户增加或扣减积分（运维用）")
    p.add_argument("--user", required=True, help="用户昵称或用户 id（数字）")
    p.add_argument("--points", type=int, required=True, help="积分变动量：正数增加，负数扣减（如 -5000）")
    return p.parse_args()


async def main():
    args = parse_args()
    if args.points == 0:
        print("--points 不能为 0")
        sys.exit(1)

    user_ident = args.user.strip()
    by_id = user_ident.isdigit()

    async with AsyncSessionLocal() as session:
        if by_id:
            r = await session.execute(select(User).where(User.id == int(user_ident)))
        else:
            r = await session.execute(
                select(User).where(User.nickname.ilike(user_ident))
            )
        user = r.scalar_one_or_none()
        if not user:
            print(f"未找到用户: {args.user}")
            sys.exit(1)
        old_points = user.points or 0
        new_points = old_points + args.points
        if new_points < 0:
            print(f"当前积分 {old_points}，扣减 {abs(args.points)} 后将为负数，已截断为 0")
            new_points = 0
        user.points = new_points
        await session.commit()
        action = "增加" if args.points > 0 else "扣减"
        print(f"用户 {user.nickname or '(无昵称)'} (id={user.id}) 积分已更新: {old_points} -> {new_points} ({action} {abs(args.points)})")


if __name__ == "__main__":
    asyncio.run(main())
