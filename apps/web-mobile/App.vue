<script setup>
</script>

<template>
  <view class="app">
    <page-meta :root-font-size="16" />
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
