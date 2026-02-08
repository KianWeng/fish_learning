<template>
  <view class="page">
    <view class="card">
      <view class="title">微信一键登录</view>
      <view class="desc">使用微信账号快速登录错题本</view>
      <button class="btn-login" @click="onLogin">微信一键登录</button>
      <view class="tip">登录即表示同意用户协议与隐私政策</view>
    </view>
  </view>
</template>

<script setup>
import request from '@/api/request.js'

async function onLogin() {
  try {
    const { code } = await uni.login({ provider: 'weixin' })
    if (!code) {
      uni.showToast({ title: '获取登录态失败', icon: 'none' })
      return
    }
    const res = await request.post('/auth/wechat/login', { code })
    uni.setStorageSync('token', res.token)
    uni.setStorageSync('user', res.user)
    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => {
      uni.switchTab({ url: '/pages/my/index' })
    }, 500)
  } catch (e) {
    uni.showToast({ title: e.message || '登录失败', icon: 'none' })
  }
}
</script>

<style scoped>
.page { min-height: 100vh; background: linear-gradient(180deg, #e8f4ff 0%, #f5f6fa 40%); padding: 120rpx 48rpx; box-sizing: border-box; }
.card { background: #fff; border-radius: 32rpx; padding: 64rpx 48rpx; box-shadow: 0 8rpx 40rpx rgba(0,0,0,0.08); }
.title { font-size: 40rpx; font-weight: 600; color: #333; text-align: center; margin-bottom: 16rpx; }
.desc { font-size: 28rpx; color: #999; text-align: center; margin-bottom: 64rpx; }
.btn-login { width: 100%; height: 96rpx; line-height: 96rpx; background: #07c160; color: #fff; font-size: 32rpx; border-radius: 48rpx; border: none; }
.btn-login::after { border: none; }
.tip { font-size: 24rpx; color: #999; text-align: center; margin-top: 32rpx; }
</style>
