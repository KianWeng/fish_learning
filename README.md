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
| `DATABASE_URL` | PostgreSQL 连接串 |
| `COZE_API_KEY` | Coze PAT（鉴权），拍照识题优先走 Coze 工作流 |
| `COZE_WORKFLOW_ID` | Coze 工作流 ID |
| `COZE_IMAGE_PARAMETER` | 工作流中图片输入参数名，默认 `image` |
| `OPENAI_API_KEY` | 大模型 API Key（未配置 Coze 时或 PDF 解析使用） |
| `DASHSCOPE_API_KEY` | 可选，与 `OPENAI_API_KEY` 二选一：阿里百炼 DashScope Key，会合并为同一套 OpenAI 兼容调用 |
| `OPENAI_BASE_URL` | 大模型 OpenAI 兼容 base URL，默认 `https://coding.dashscope.aliyuncs.com/v1`（百炼） |
| `OPENAI_VISION_MODEL` | 识图多模态模型，默认 `qwen-vl-plus` |
| `OPENAI_CHAT_MODEL` | 纯文本任务（报告、PDF 解析页），默认 `qwen-plus` |
| `VISION_IMAGE_PRIORITY` | 识图顺序：`bailian`（默认，百炼/OpenAI 兼容先）或 `coze`（Coze 先） |
| `STORAGE_LOCAL_PATH` | 本地存储路径，默认 `./uploads`（其下分 `avatars/`、`questions/`、`pdfs/`） |
| `FORCE_HTTPS` | 设为 `true` 时，若请求为 http（如 `X-Forwarded-Proto=http`）则 301 重定向到 https |
| `API_BASE_URL` | 可选，对外 API 基地址（用于生成绝对 URL） |

### HTTPS 与文件访问

- **文件存储**：按用户分目录 `uploads/<storage_key>/avatars|questions|pdfs/`，`storage_key` 由用户微信 **openid** 经安全化得到（仅字母数字时直接用，否则用 sha256 前 32 位），URL 形如 `/files/avatars/<storage_key>/<filename>`；不暴露内部 user_id，统计逻辑（`storage_used_bytes`）不变。
- 题目图片为公开访问，PDF 需登录后访问。

## 生产部署（HTTPS）

你已有 HTTPS 证书时，可用以下任一方式部署，并设置 `FORCE_HTTPS=true`（用反向代理时）。

### 方式一：Nginx 反向代理（推荐）

Nginx 对外 443，把请求转发到本机 uvicorn（如 8000 端口），并设置 `X-Forwarded-Proto`、`X-Forwarded-For` 等，便于应用做 HTTPS 重定向和日志。

1. 安装 Nginx（如 Ubuntu：`sudo apt install nginx`）。
2. 新建站点配置（如 `/etc/nginx/sites-available/mistake-book-api`）：

```nginx
server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate     /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

3. 启用并重载 Nginx：

```bash
sudo ln -s /etc/nginx/sites-available/mistake-book-api /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

4. 后端用 systemd 或 supervisor 跑 uvicorn（仅监听本地，不绑证书），例如：

```bash
cd /path/to/mistake_book/apps/api
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

5. 在 `.env` 中设置 `FORCE_HTTPS=true`（若仍有 http 访问则应用内会 301 到 https）。

### 方式二：Caddy 反向代理

Caddy 配置更简洁，若你已有证书可手动指定：

```bash
# Caddyfile 示例
tls /path/to/fullchain.pem /path/to/privkey.pem
reverse_proxy 127.0.0.1:8000
```

Caddy 会转发 `X-Forwarded-Proto`。同样在 `.env` 中设置 `FORCE_HTTPS=true`，后端 uvicorn 只监听 `127.0.0.1:8000`。

### 方式三：Uvicorn 直连 HTTPS（单机简单部署）

不经过反向代理，直接让 uvicorn 使用你的证书：

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 443 \
  --ssl-keyfile=/path/to/privkey.pem \
  --ssl-certfile=/path/to/fullchain.pem
```

- 监听 443 通常需 root 或 `setcap` 赋权。
- 不经过 Nginx/Caddy 时，静态资源、限流、多实例等需自行处理；适合单实例、流量不大的场景。
- 此时应用内 `X-Forwarded-Proto` 可能为 http（直连无代理），可按需将 `FORCE_HTTPS` 设为 `false` 或仅在前端使用 https 地址。

## 功能概览

1. **拍照添加错题**：上传图片 → Coze 工作流（或 OpenAI）识别题目并输出 JSON（题目/解析/答案）→ 选择科目/章节保存
2. **科目与章节**：在「科目管理」中增删改科目，进入某科目可管理章节
3. **错题列表与详情**：按科目/章节筛选，点击进入详情查看题目与解析
4. **每日复习**：按艾宾浩斯曲线，展示今日待复习题目，选择「记得/模糊/忘记」后更新下次复习日
5. **PDF 导入**：选择 PDF 与目标科目/章节，按页解析为错题并入库
