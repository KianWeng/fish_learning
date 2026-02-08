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
- **微信小程序**：先执行 `npm run dev:mp-weixin`，再用**微信开发者工具**打开目录 **`dist/dev/mp-weixin`**（必须打开编译后的目录，不要打开项目源码根目录）。

### 微信模拟器启动失败时请按下面排查

1. **必须打开编译输出目录**  
   在微信开发者工具里，导入项目时选择的是 **`apps/web-mobile/dist/dev/mp-weixin`**，而不是 `apps/web-mobile` 或 `apps/web-mobile/src`。未编译或打开错目录会导致「模拟器启动失败」。

2. **先编译再打开**  
   在项目根目录 `apps/web-mobile` 下执行：
   ```bash
   npm run dev:mp-weixin
   ```
   等终端里出现“编译完成”或类似提示后，再用微信开发者工具打开 `dist/dev/mp-weixin`。

3. **开启服务端口**（若用 HBuilderX 或 CLI 自动打开工具）  
   微信开发者工具 → **设置 → 安全设置** → 勾选 **开启服务端口**。

4. **清理缓存后重试**  
   微信开发者工具 → **设置 → 外观设置** → **清理缓存** → 全部清理，然后关闭并重新打开项目（仍要打开 `dist/dev/mp-weixin`）。

5. **本机调试可不填 AppID**  
   `manifest.json` 里 `mp-weixin.appid` 为空时，在微信开发者工具里选「测试号」或「不使用 AppID」即可本地预览。

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
