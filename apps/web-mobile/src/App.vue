<script>
export default {
  name: 'App',
  // Options API 便于小程序框架正确挂载 getApp().$vm，减轻真机栈溢出
}
</script>

<template>
  <view class="app">
    <!-- #ifdef H5 -->
    <page-meta root-font-size="16" />
    <!-- #endif -->
    <slot />
  </view>
</template>

<style>
/* 全局设计令牌：与首页统一，各页通过 var() 引用 */
page, .app {
  --primary: #4A90E2;
  --primary-light: #66B2FF;
  --primary-bg: #E3F2FD;
  --success: #A5D6A7;
  --warn: #FFCC80;
  --text: #333;
  --text-secondary: #666;
  --text-hint: #999;
  --bg-page: #F5F5F5;
  --bg-card: #fff;
  --shadow: 0 2rpx 16rpx rgba(0,0,0,0.05);
  --shadow-card: 0 4rpx 20rpx rgba(0,0,0,0.06);
}
.app {
  min-height: 100vh;
  background: var(--bg-page);
}
page {
  font-size: 16px;
  background: var(--bg-page);
}
</style>
