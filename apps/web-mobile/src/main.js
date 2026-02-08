import App from './App.vue'
// 小程序真机栈限制更严，用 createApp 减少初始化调用栈；H5/其他端仍用 createSSRApp
// #ifdef MP-WEIXIN
import { createApp as createVueApp } from 'vue'
// #endif
// #ifndef MP-WEIXIN
import { createSSRApp } from 'vue'
// #endif

export function createApp() {
  // #ifdef MP-WEIXIN
  const app = createVueApp(App)
  // #endif
  // #ifndef MP-WEIXIN
  const app = createSSRApp(App)
  // #endif
  return { app }
}
