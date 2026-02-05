# 错题本 - 跨平台应用

支持 **iOS**、**Android**、**微信小程序**、**H5 网页** 的错题本应用。功能包括：拍照添加错题（大模型分析）、科目与章节管理、PDF 导入、艾宾浩斯每日复习。

## 项目结构

- **apps/api**：Python FastAPI 后端，提供 REST API、大模型调用、PDF 解析、复习调度
- **apps/web-mobile**：uni-app (Vue3) 前端，一套代码多端运行

## 快速开始

### 1. 后端

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

创建 PostgreSQL 数据库（如 `mistake_book`），配置环境变量（可选，见 `apps/api/.env.example`）：

```bash
# 复制并编辑
cp apps/api/.env.example apps/api/.env
# 至少设置 database_url、openai_api_key（用于拍照识题与 PDF 解析）
```

执行迁移并启动（需先激活虚拟环境，或用 `.venv/bin/python`）：

```bash
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档：http://localhost:8000/docs

### 2. 前端（H5）

```bash
cd apps/web-mobile
npm install
npm run dev:h5
```

浏览器打开 http://localhost:5173。确保后端已启动，前端通过代理访问 `/api`。

### 3. 微信小程序

```bash
cd apps/web-mobile
npm run dev:mp-weixin
```

用微信开发者工具打开 `dist/dev/mp-weixin`，并在小程序后台配置 request 合法域名（或本地勾选不校验）。详见 `apps/web-mobile/README.md`。

## 环境变量（后端）

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | PostgreSQL 连接串，默认 `postgresql+asyncpg://postgres:postgres@localhost:5432/mistake_book` |
| `OPENAI_API_KEY` | 大模型 API Key（OpenAI 或国内兼容接口） |
| `OPENAI_BASE_URL` | 可选，大模型 base URL |
| `STORAGE_LOCAL_PATH` | 本地存储路径，默认 `./uploads` |

## 功能概览

1. **拍照添加错题**：上传图片 → 大模型识别题目并生成解析与答案 → 选择科目/章节保存
2. **科目与章节**：在「科目管理」中增删改科目，进入某科目可管理章节
3. **错题列表与详情**：按科目/章节筛选，点击进入详情查看题目与解析
4. **每日复习**：按艾宾浩斯曲线，展示今日待复习题目，选择「记得/模糊/忘记」后更新下次复习日
5. **PDF 导入**：选择 PDF 与目标科目/章节，按页解析为错题并入库
