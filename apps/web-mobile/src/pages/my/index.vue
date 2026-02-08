<template>
  <view class="page">
    <view class="profile">
      <view class="avatar-wrap">
        <text class="avatar-placeholder">👤</text>
      </view>
      <text class="nickname">{{ userInfo.nickname || '未设置昵称' }}</text>
      <text class="desc" v-if="userInfo.desc">{{ userInfo.desc }}</text>
    </view>

    <view class="menu">
      <view class="menu-item" @click="goStats">
        <text class="menu-icon">📊</text>
        <text class="menu-text">数据统计</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="goSubjects">
        <text class="menu-icon">📁</text>
        <text class="menu-text">科目管理</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="goImportPdf">
        <text class="menu-icon">📄</text>
        <text class="menu-text">导入 PDF</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <view class="tabbar-placeholder" />
    <TabBar current="my" />
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import TabBar from '@/components/TabBar.vue'

const userInfo = ref({ nickname: '', desc: '' })

onMounted(() => {
  // 可从本地存储或后端拉取用户信息
  try {
    const nick = uni.getStorageSync('user_nickname')
    const desc = uni.getStorageSync('user_desc')
    if (nick) userInfo.value.nickname = nick
    if (desc) userInfo.value.desc = desc
  } catch (e) {}
})

function goStats() {
  uni.navigateTo({ url: '/pages/stats/index' })
}

function goSubjects() {
  uni.navigateTo({ url: '/pages/subjects/list' })
}

function goImportPdf() {
  uni.navigateTo({ url: '/pages/import/pdf' })
}
</script>

<style scoped>
.page { padding: 24rpx 24rpx 140rpx; background: #f0f1f5; min-height: 100vh; }
.profile { background: #fff; border-radius: 24rpx; padding: 48rpx; text-align: center; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.06); margin-bottom: 24rpx; }
.avatar-wrap { width: 160rpx; height: 160rpx; margin: 0 auto 24rpx; border-radius: 50%; background: #e8f4ff; display: flex; align-items: center; justify-content: center; }
.avatar-placeholder { font-size: 80rpx; }
.nickname { font-size: 36rpx; font-weight: 600; color: #333; display: block; }
.desc { font-size: 26rpx; color: #999; margin-top: 12rpx; display: block; }
.menu { background: #fff; border-radius: 24rpx; overflow: hidden; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.06); }
.menu-item { display: flex; align-items: center; padding: 32rpx 24rpx; border-bottom: 1rpx solid #f0f0f0; }
.menu-item:last-child { border-bottom: none; }
.menu-icon { font-size: 40rpx; margin-right: 24rpx; }
.menu-text { flex: 1; font-size: 30rpx; color: #333; }
.menu-arrow { font-size: 36rpx; color: #999; }
.tabbar-placeholder { height: 120rpx; }
</style>
