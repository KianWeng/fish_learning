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

### 真机运行报错（模拟器正常、真机 Maximum call stack size exceeded / getApp().$vm）

真机 JS 栈限制比模拟器更严，同一段框架初始化代码在真机上更容易栈溢出。

1. **已做优化**：  
   - **小程序端**：`App.vue` 通过条件编译**不在小程序里使用 page-meta**（仅 H5 使用），避免 `getApp().$vm` 与栈溢出；入口 `main.js` 在 **MP-WEIXIN** 下使用 `createApp` 替代 `createSSRApp`，减轻真机初始化调用栈。  
   - **依赖**：已升级为 `@dcloudio/*` 的 **3.0.0-alpha-4080720251125001** 与 `@dcloudio/types@3.4.19`，建议先 `npm install` 后重新编译并在真机预览/体验版测试。  
   - **config.js** 不访问 `window`，避免逻辑层异常。  
2. **若仍出现 LifeCycle.load / 栈溢出 / $vm**：可再试 `npx @dcloudio/uvm@latest alpha` 选更高版本；或把 `vite` 改为 `"5.0.10"` 后 `npm install --legacy-peer-deps` 再编译。  
3. **排查方向**：真机调试看报错顺序；检查递归、setData 循环、生命周期互相触发。若改用 `createApp` 后出现其它异常，可将 `main.js` 中 MP-WEIXIN 分支改回 `createSSRApp`。

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

5. **存储扩容（积分 + 激励视频广告）**  
   个人小程序无法使用微信支付，本应用通过「观看激励视频得积分 → 积分兑换扩容包」实现扩容。  
   - 在微信公众平台开通 **流量主**，创建 **激励式视频广告** 广告位，获得广告位 ID。  
   - 在项目根目录 `.env` 中配置：`VITE_AD_REWARD_UNIT_ID=你的广告位ID`（如 `adunit-xxxx`），重新执行 `npm run dev:mp-weixin` 或 `npm run build:mp-weixin`。  
   - 用户进入「我的 → 存储扩容」可看到当前积分、观看广告获积分、以及用积分兑换 50MB/100MB/200MB 扩容包（有效期 1 年）。  
   - 后端通过 `points_per_ad_reward`、`max_ad_rewards_per_day` 控制每次奖励积分和每日观看上限（见 `apps/api/.env.example`）。

### H5 部署

1. 将 `dist/build/h5` 部署到任意静态服务器（Nginx、OSS、Vercel 等）
2. 若前后端同域，可配置 Nginx 将 `/api` 反向代理到后端；若不同域，需修改 `api/request.js` 和 `api/questions.js`、`api/import.js` 中的 `BASE_URL` 为实际后端地址，并确保后端开启 CORS

### App 打包

1. 使用 HBuilderX 打开本目录，或使用 CLI 构建后导入
2. 在 HBuilderX 中「发行 - 原生 App - 云打包」或「本地打包」
3. 打包前在 `manifest.json` 的 `app-plus` 中配置应用名称、图标等
4. 若 App 访问的后端与 H5 不同，需在代码中根据运行平台设置 `BASE_URL`（可条件编译）

## 错题详情图片不显示 - 排查步骤

1. **在详情页打开调试信息**  
   进入某条错题的详情页，点击底部「**显示调试信息**」。会显示当前拼接出的图片完整地址。  
   - 若显示「(未拼接)」：说明接口返回的 `image_url` 为空或未正确赋值，需查后端该条错题是否保存了 `image_url`。  
   - 若有地址：长按该地址复制，在**电脑浏览器**新标签页粘贴打开。  
     - **浏览器能打开**：说明后端静态文件正常，问题多半在小程序/前端的域名或 `<image>` 加载限制。  
     - **浏览器打不开**：说明后端未正确保存文件或未挂载静态目录，需查 `apps/api` 的 `storage` 与 `main.py` 的 StaticFiles。

2. **看控制台输出**  
   微信开发者工具 → 打开「调试器」→ Console。进入错题详情页后应看到：  
   `[错题详情] image_url from API: ...`、`API_BASE_URL: ...`、`imageFullUrl: ...`。  
   - 若出现 `[错题详情] 图片加载失败`：说明 `<image>` 请求该 URL 失败，常见原因见下。

3. **微信小程序域名**  
   小程序里 `<image src="https://...">` 的域名必须在 **微信公众平台 → 开发 → 开发管理 → 开发设置 → 服务器域名** 中配置：  
   - **request 合法域名**：填你的后端 API 域名（如 `https://your-api.com`），必须 HTTPS。  
   - 若仍不显示，可再在 **downloadFile 合法域名** 里添加同一域名。  
   本地开发时可在开发者工具中勾选「不校验合法域名」，此时若图片能显示，则基本可确定是域名未配置。

4. **确认后端有图**  
   - 看 `apps/api` 的 `storage_local_path`（默认 `./uploads`）下是否有 `images/xxx.jpg`。  
   - 看数据库该条错题的 `image_url` 字段是否为 `/uploads/images/xxx.jpg` 这类值。

5. **H5 时**  
   若用代理（如 `VITE_API_BASE_URL=/api`），图片地址会是 `/api/uploads/...`，需确认 vite 的 proxy 会把 `/api` 转发到后端，且后端静态路由是 `/uploads`（不是 `/api/uploads`）。若代理只转发了 `/api` 下接口，需单独为 `/api/uploads` 做转发或改用完整后端地址。

## 接口基础地址

- 开发 H5 时，通过 vite 代理将 `/api` 转发到 `http://localhost:8000`
- 小程序 / App 需使用可公网访问的后端地址，并在对应配置中填写
