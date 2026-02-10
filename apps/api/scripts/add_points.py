"""
运维脚本：为指定用户增加积分。
用法：
  python scripts/add_points_zephyr.py --user Zephyr --points 10000
  python scripts/add_points_zephyr.py --user 1 --points 5000   # 按用户 id
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
    p = argparse.ArgumentParser(description="为指定用户增加积分（运维用）")
    p.add_argument("--user", required=True, help="用户昵称或用户 id（数字）")
    p.add_argument("--points", type=int, required=True, help="要增加的积分数（正整数）")
    return p.parse_args()


async def main():
    args = parse_args()
    if args.points <= 0:
        print("--points 须为正整数")
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
        user.points = old_points + args.points
        await session.commit()
        # 提交后 ORM 可能刷新，直接打印计算后的值
        print(f"用户 {user.nickname or '(无昵称)'} (id={user.id}) 积分已更新: {old_points} -> {old_points + args.points}")


if __name__ == "__main__":
    asyncio.run(main())
