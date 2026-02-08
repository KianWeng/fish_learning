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
.app {
  min-height: 100vh;
  background: #f8f8f8;
}
page {
  font-size: 16px;
  background: #f8f8f8;
}
</style>
