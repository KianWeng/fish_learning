<template>
  <view class="tabbar">
    <view class="item" @click="go('/pages/index/index')">
      <text class="icon">🏠</text>
      <text class="label" :class="{ active: current === 'index' }">首页</text>
    </view>
    <view class="item" @click="go('/pages/questions/list')">
      <text class="icon">📚</text>
      <text class="label" :class="{ active: current === 'questions' }">错题本</text>
    </view>
    <view class="item center" @click="go('/pages/questions/add')">
      <view class="camera-btn">
        <text class="camera-icon">📷</text>
      </view>
      <text class="label">拍照</text>
    </view>
    <view class="item" @click="go('/pages/review/index')">
      <text class="icon">🔄</text>
      <text class="label" :class="{ active: current === 'review' }">复习</text>
    </view>
    <view class="item" @click="go('/pages/my/index')">
      <text class="icon">👤</text>
      <text class="label" :class="{ active: current === 'my' }">我的</text>
    </view>
  </view>
</template>

<script setup>
defineProps({ current: { type: String, default: '' } })

function go(url) {
  uni.switchTab ? uni.switchTab({ url }) : uni.navigateTo({ url })
}
</script>

<style scoped>
.tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 120rpx;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-around;
  box-shadow: 0 -2rpx 16rpx rgba(0,0,0,0.06);
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 100;
}
.item { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; }
.icon { font-size: 40rpx; }
.item.center .label { color: #999; }
.label { font-size: 22rpx; color: #999; margin-top: 4rpx; }
.label.active { color: #1989fa; font-weight: 500; }
.item.center .camera-btn {
  width: 96rpx; height: 96rpx;
  background: linear-gradient(135deg, #1989fa 0%, #0d6ef5 100%);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin-top: -40rpx;
  box-shadow: 0 8rpx 24rpx rgba(25,137,250,0.4);
}
.item.center .camera-icon { font-size: 44rpx; }
</style>
