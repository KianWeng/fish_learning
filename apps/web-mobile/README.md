# 错题本 - 跨端前端

uni-app (Vue3) 项目，支持编译到 **H5**、**微信小程序**、**App（iOS/Android）**。

## 环境

- Node.js 18+
- npm 或 pnpm

## 安装

```bash
cd apps/web-mobile
npm install
```

## 开发

- **H5**：`npm run dev:h5`，浏览器访问 http://localhost:5173（需同时启动后端并配置代理，见 vite.config.js）
- **微信小程序**：`npm run dev:mp-weixin`，用微信开发者工具打开 `dist/dev/mp-weixin` 目录

## 构建

- **H5**：`npm run build:h5`，产物在 `dist/build/h5`
- **微信小程序**：`npm run build:mp-weixin`，用微信开发者工具打开 `dist/build/mp-weixin` 上传
- **App**：`npm run build:app`，需在 HBuilderX 中打开项目进行云打包或本地打包

## 多端配置说明

### 微信小程序

1. 在微信公众平台申请小程序，获得 AppID
2. 在 `manifest.json` 的 `mp-weixin.appid` 中填写 AppID
3. 在小程序后台「开发 - 开发管理 - 开发设置」中配置 **request 合法域名**：填写你的后端 API 域名（如 `https://your-api.com`），且必须 HTTPS
4. 本地开发时可在开发者工具中勾选「不校验合法域名」

### H5 部署

1. 将 `dist/build/h5` 部署到任意静态服务器（Nginx、OSS、Vercel 等）
2. 若前后端同域，可配置 Nginx 将 `/api` 反向代理到后端；若不同域，需修改 `api/request.js` 和 `api/questions.js`、`api/import.js` 中的 `BASE_URL` 为实际后端地址，并确保后端开启 CORS

### App 打包

1. 使用 HBuilderX 打开本目录，或使用 CLI 构建后导入
2. 在 HBuilderX 中「发行 - 原生 App - 云打包」或「本地打包」
3. 打包前在 `manifest.json` 的 `app-plus` 中配置应用名称、图标等
4. 若 App 访问的后端与 H5 不同，需在代码中根据运行平台设置 `BASE_URL`（可条件编译）

## 接口基础地址

- 开发 H5 时，通过 vite 代理将 `/api` 转发到 `http://localhost:8000`
- 小程序 / App 需使用可公网访问的后端地址，并在对应配置中填写
