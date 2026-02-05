<template>
  <view class="page">
    <view class="nav-list">
      <navigator url="/pages/subjects/list" class="nav-item">科目与章节</navigator>
      <navigator url="/pages/questions/list" class="nav-item">错题列表</navigator>
      <navigator url="/pages/questions/add" class="nav-item">拍照添加</navigator>
      <navigator url="/pages/review/index" class="nav-item">每日复习</navigator>
      <navigator url="/pages/import/pdf" class="nav-item">导入PDF</navigator>
    </view>
  </view>
</template>

<script setup>
</script>

<style scoped>
.page { padding: 40rpx; }
.nav-list { display: flex; flex-direction: column; gap: 24rpx; }
.nav-item {
  padding: 32rpx; background: #fff; border-radius: 16rpx;
  font-size: 32rpx; text-align: center; box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06);
}
</style>
