# 错题本 API

FastAPI 后端，提供科目/章节/错题/上传/复习等接口。

## 环境

- Python 3.11+
- PostgreSQL（创建数据库 `mistake_book`）

## 安装与运行

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# 可选：复制 .env.example 为 .env 并修改
python -m alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档: http://localhost:8000/docs

## 测试 Coze 工作流

配置好 `.env` 中的 `COZE_API_KEY` 和 `COZE_WORKFLOW_ID` 后，可运行：

```bash
cd apps/api
.venv/bin/python scripts/test_coze.py                  # 使用内置最小测试图（测连通性）
.venv/bin/python scripts/test_coze.py path/to/图.jpg  # 使用本地错题图片
```

脚本会依次执行：上传图片 -> 调用工作流 -> 解析 JSON 输出，并打印各步结果。

## 数据库迁移

（在已激活的虚拟环境中，或使用 `.venv/bin/python -m alembic`）

```bash
python -m alembic revision --autogenerate -m "描述"
python -m alembic upgrade head
```
