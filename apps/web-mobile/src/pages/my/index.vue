<template>
  <view class="page">
    <view class="profile">
      <view class="avatar-wrap" @click="goLoginIfNeed">
        <image v-if="userInfo.avatar_url" class="avatar-img" :src="userInfo.avatar_url" mode="aspectFill" />
        <text v-else class="avatar-placeholder">👤</text>
      </view>
      <text class="nickname">{{ userInfo.nickname || (isLoggedIn ? '微信用户' : '未登录') }}</text>
      <text class="desc" v-if="userInfo.desc">{{ userInfo.desc }}</text>
      <view class="auth-row">
        <button v-if="!isLoggedIn" class="btn-auth" @click="goLogin">去登录</button>
        <button v-else class="btn-auth secondary" @click="logout">退出登录</button>
      </view>
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
import { ref, computed, onMounted } from 'vue'
import TabBar from '@/components/TabBar.vue'
import request from '@/api/request.js'

const userInfo = ref({ nickname: '', desc: '', avatar_url: '' })
const token = ref('')

const isLoggedIn = computed(() => !!token.value)

onMounted(() => {
  try {
    token.value = uni.getStorageSync('token') || ''
    const u = uni.getStorageSync('user')
    if (u && typeof u === 'object') {
      userInfo.value.nickname = u.nickname || ''
      userInfo.value.avatar_url = u.avatar_url || ''
    }
    if (!userInfo.value.nickname) {
      const nick = uni.getStorageSync('user_nickname')
      if (nick) userInfo.value.nickname = nick
    }
    const desc = uni.getStorageSync('user_desc')
    if (desc) userInfo.value.desc = desc
  } catch (e) {}
  if (token.value) fetchUser()
})

async function fetchUser() {
  try {
    const u = await request.get('/auth/me')
    userInfo.value.nickname = u.nickname || userInfo.value.nickname
    userInfo.value.avatar_url = u.avatar_url || ''
    uni.setStorageSync('user', u)
  } catch (e) {}
}

function goLogin() {
  uni.navigateTo({ url: '/pages/auth/login' })
}

function goLoginIfNeed() {
  if (!isLoggedIn.value) goLogin()
}

function logout() {
  uni.removeStorageSync('token')
  uni.removeStorageSync('user')
  token.value = ''
  userInfo.value = { nickname: '', desc: '', avatar_url: '' }
  uni.showToast({ title: '已退出', icon: 'none' })
}

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
.avatar-wrap { width: 160rpx; height: 160rpx; margin: 0 auto 24rpx; border-radius: 50%; background: #e8f4ff; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.avatar-img { width: 100%; height: 100%; }
.avatar-placeholder { font-size: 80rpx; }
.nickname { font-size: 36rpx; font-weight: 600; color: #333; display: block; }
.desc { font-size: 26rpx; color: #999; margin-top: 12rpx; display: block; }
.auth-row { margin-top: 24rpx; }
.btn-auth { width: 240rpx; height: 64rpx; line-height: 64rpx; font-size: 28rpx; border-radius: 32rpx; background: #07c160; color: #fff; border: none; }
.btn-auth::after { border: none; }
.btn-auth.secondary { background: transparent; color: #999; border: 1rpx solid #ddd; }
.menu { background: #fff; border-radius: 24rpx; overflow: hidden; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.06); }
.menu-item { display: flex; align-items: center; padding: 32rpx 24rpx; border-bottom: 1rpx solid #f0f0f0; }
.menu-item:last-child { border-bottom: none; }
.menu-icon { font-size: 40rpx; margin-right: 24rpx; }
.menu-text { flex: 1; font-size: 30rpx; color: #333; }
.menu-arrow { font-size: 36rpx; color: #999; }
.tabbar-placeholder { height: 120rpx; }
</style>
