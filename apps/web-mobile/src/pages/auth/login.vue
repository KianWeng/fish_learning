<template>
  <view class="page">
    <view class="card">
      <view class="title">微信登录</view>
      <view class="desc">设置你的昵称和头像后登录</view>

      <view class="form">
        <view class="avatar-row">
          <text class="label">头像</text>
          <button class="avatar-btn" open-type="chooseAvatar" @chooseavatar="onChooseAvatar">
            <CachedImage v-if="avatarUrl" img-class="avatar-img" :src="avatarUrl" mode="aspectFill" img-style="width: 100%; height: 100%; display: block;" />
            <text v-else class="avatar-placeholder">点击选择</text>
          </button>
        </view>
        <view class="nickname-row">
          <text class="label">昵称</text>
          <input
            v-model="nickname"
            class="nickname-input"
            type="nickname"
            placeholder="请输入昵称或使用微信昵称"
            placeholder-class="placeholder"
          />
        </view>
      </view>

      <button class="btn-login" @click="onLogin">微信一键登录</button>
      <view class="tip">登录即表示同意用户协议与隐私政策</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import CachedImage from '@/components/CachedImage.vue'
import request from '@/api/request.js'
import { API_BASE_URL } from '@/config.js'

const nickname = ref('')
const avatarUrl = ref('')  // 本地预览：临时路径或已上传的 URL
let avatarTempPath = ''   // 选择头像后的临时路径，用于上传

function onChooseAvatar(e) {
  const { avatarUrl: path } = e.detail || {}
  if (path) {
    avatarTempPath = path
    avatarUrl.value = path
  }
}

async function uploadAvatar() {
  if (!avatarTempPath) return null
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: API_BASE_URL + '/upload/image',
      filePath: avatarTempPath,
      name: 'file',
      header: {},
      success: (res) => {
        try {
          const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
          console.log('[登录页] 上传头像响应:', res.statusCode, data)
          if (data.url) {
            const fullUrl = API_BASE_URL + data.url
            console.log('[登录页] 头像完整 URL:', fullUrl)
            resolve(fullUrl)
          } else {
            console.warn('[登录页] 上传头像无 url:', data)
            resolve(null)
          }
        } catch (e) {
          console.warn('[登录页] 解析上传响应失败:', e)
          resolve(null)
        }
      },
      fail: (err) => {
        console.warn('[登录页] 上传头像失败:', err)
        resolve(null)
      },
    })
  })
}

async function onLogin() {
  try {
    const { code } = await uni.login({ provider: 'weixin' })
    if (!code) {
      uni.showToast({ title: '获取登录态失败', icon: 'none' })
      return
    }
    let avatar_url = null
    if (avatarTempPath) {
      uni.showLoading({ title: '上传头像…' })
      avatar_url = await uploadAvatar()
      uni.hideLoading()
    }
    const payload = {
      code,
      nickname: nickname.value.trim() || null,
      avatar_url,
    }
    console.log('[登录页] 登录请求 payload:', { ...payload, code: '***' })
    const res = await request.post('/auth/wechat/login', payload)
    console.log('[登录页] 登录成功 res.user:', res.user, 'avatar_url:', res.user?.avatar_url)
    uni.setStorageSync('token', res.token)
    uni.setStorageSync('user', res.user)
    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => {
      uni.reLaunch({ url: '/pages/my/index' })
    }, 500)
  } catch (e) {
    uni.showToast({ title: e.message || '登录失败', icon: 'none' })
  }
}
</script>

<style scoped>
.page { min-height: 100vh; background: linear-gradient(180deg, var(--primary-bg) 0%, var(--bg-page) 40%); padding: 120rpx 48rpx 80rpx; box-sizing: border-box; }
.card { background: var(--bg-card); border-radius: 32rpx; padding: 48rpx 48rpx 64rpx; box-shadow: var(--shadow-card); }
.title { font-size: 40rpx; font-weight: 600; color: var(--text); text-align: center; margin-bottom: 16rpx; }
.desc { font-size: 28rpx; color: var(--text-hint); text-align: center; margin-bottom: 48rpx; }
.form { margin-bottom: 48rpx; }
.avatar-row { display: flex; align-items: center; margin-bottom: 32rpx; }
.avatar-row .label { width: 120rpx; font-size: 30rpx; color: var(--text); }
.avatar-btn { width: 160rpx; height: 160rpx; border-radius: 50%; overflow: hidden; padding: 0; margin: 0; background: var(--bg-page); border: 2rpx dashed var(--text-hint); position: relative; }
.avatar-btn::after { border: none; }
.avatar-img {
  position: absolute;
  left: 0; top: 0; right: 0; bottom: 0;
  width: 100% !important;
  height: 100% !important;
  display: block;
}
.avatar-placeholder { font-size: 24rpx; color: var(--text-hint); }
.nickname-row { display: flex; align-items: center; }
.nickname-row .label { width: 120rpx; font-size: 30rpx; color: var(--text); }
.nickname-input { flex: 1; height: 80rpx; padding: 0 24rpx; font-size: 30rpx; background: var(--bg-page); border-radius: 12rpx; }
.placeholder { color: var(--text-hint); }
.btn-login { width: 100%; height: 96rpx; line-height: 96rpx; background: var(--primary); color: #fff; font-size: 32rpx; border-radius: 48rpx; border: none; }
.btn-login::after { border: none; }
.tip { font-size: 24rpx; color: var(--text-hint); text-align: center; margin-top: 32rpx; }
</style>
