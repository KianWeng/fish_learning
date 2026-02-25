"""
测试识图：与线上一致，使用 K12 系统 prompt。支持豆包 Doubao（Ark）或 OpenAI。
用法（在 apps/api 目录下）：
  python scripts/test_deepseek_vision.py path/to/image.jpg
  python scripts/test_deepseek_vision.py   # 使用 uploads 下任意一张题目图
配置 ARK_API_KEY 时走豆包，否则走 OPENAI_API_KEY。
"""
import argparse
import asyncio
import base64
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.services.llm import _get_question_system_prompt, _analyze_via_ark


def find_one_image() -> Path | None:
    """在 uploads 下找一张 jpg 作为默认测试图。"""
    base = Path(__file__).resolve().parent.parent / "uploads"
    if not base.is_dir():
        return None
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        for p in base.rglob(ext):
            if p.is_file() and "questions" in p.parts:
                return p
    return None


def load_image_b64(path: Path) -> str:
    raw = path.read_bytes()
    return base64.b64encode(raw).decode("utf-8")


def image_data_url(path: Path) -> str:
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("utf-8")
    suffix = path.suffix.lower()
    mime = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png" if suffix == ".png" else "image/jpeg"
    return f"data:{mime};base64,{b64}"


async def main():
    parser = argparse.ArgumentParser(description="测试 DeepSeek/OpenAI 识图")
    parser.add_argument("image", nargs="?", help="图片路径（可选，不传则用 uploads 下题目图）")
    args = parser.parse_args()

    if args.image:
        path = Path(args.image)
        if not path.is_file():
            print(f"文件不存在: {path}")
            sys.exit(1)
    else:
        path = find_one_image()
        if not path:
            print("未指定图片且 uploads 下未找到题目图，请执行: python scripts/test_deepseek_vision.py <图片路径>")
            sys.exit(1)
        print(f"使用默认图片: {path}")

    use_ark = bool(getattr(settings, "ark_api_key", None))
    if not use_ark and not settings.openai_api_key:
        print("未配置 ARK_API_KEY 或 OPENAI_API_KEY，请在 .env 中设置")
        sys.exit(1)

    image_b64 = load_image_b64(path)
    print(f"图片 base64 长度={len(image_b64)}")

    if use_ark:
        print("[豆包 Ark] 使用火山方舟 Responses API（input_image + input_text）")
        try:
            result = await _analyze_via_ark(image_b64)
            text = result.get("content", "") + (
                f"\n[analysis] {result.get('analysis', '')}" if result.get("analysis") else ""
            ) + (f"\n[answer] {result.get('answer', '')}" if result.get("answer") else "")
            print("\n========== 解析后（content/analysis/answer）==========")
            print(text[:4000])
            print("======================================================")
        except Exception as e:
            print(f"\n调用异常: {type(e).__name__}: {e}")
            sys.exit(1)
        return

    base_url = (settings.openai_base_url or "").lower()
    is_deepseek = "deepseek" in base_url
    model = getattr(settings, "openai_vision_model", None) or "gpt-4o-mini"
    data_url = image_data_url(path)
    system_prompt = _get_question_system_prompt()
    user_prompt = "请分析该错题图片，严格按系统提示中的要求只输出一个标准 JSON 对象，无任何其他内容。"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
        print(f"[系统 prompt] 已加载，长度={len(system_prompt)} 字符")
    else:
        print("[系统 prompt] 未配置，使用默认 user 指令")

    if is_deepseek:
        messages.append({"role": "user", "content": data_url})
        messages.append({"role": "user", "content": "请分析上面这张错题图片，严格按系统提示中的要求只输出一个标准 JSON 对象，无任何其他内容。"})
        print(f"[DeepSeek] message 数组：system + 两条 user（先图片，再指令）")
    else:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        })
        print(f"[OpenAI] content 数组（text + image_url）")

    print(f"base_url={settings.openai_base_url}, model={model}")
    print("请求中...")

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url or "https://api.openai.com/v1",
        )
        resp = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=2048,
        )
        text = (resp.choices[0].message.content or "").strip()
        print("\n========== 原始返回 ==========")
        print(text[:3000] + ("\n...(截断)" if len(text) > 3000 else ""))
        print("==============================")
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                obj = json.loads(m.group())
                print("\n========== 解析后 JSON ==========")
                print(json.dumps(obj, ensure_ascii=False, indent=2)[:4000])
                print("==================================")
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"\n调用异常: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
