<template>
  <view class="page" v-if="q">
    <view class="card" v-if="q.image_url">
      <image v-if="imageFullUrl" :src="imageFullUrl" mode="widthFix" class="img" @error="onImageError" />
      <view v-else class="img-placeholder">图片加载失败</view>
    </view>
    <!-- 调试用：显示图片地址，长按可复制，便于在浏览器中直接打开测试 -->
    <view class="card debug-card" v-if="q.image_url && showDebug">
      <text class="label">调试 - 图片地址</text>
      <text class="debug-url" selectable @longpress="copyImageUrl">{{ imageFullUrl || '(未拼接)' }}</text>
      <text class="debug-hint">长按复制后到浏览器打开，能打开则说明后端正常</text>
    </view>
    <view class="card">
      <text class="label">题目</text>
      <text class="content">{{ q.content }}</text>
    </view>
    <view class="card" v-if="q.analysis">
      <text class="label">解析</text>
      <text class="content">{{ q.analysis }}</text>
    </view>
    <view class="card" v-if="q.answer">
      <text class="label">答案</text>
      <text class="content">{{ q.answer }}</text>
    </view>
    <view class="meta">创建于 {{ q.created_at }}</view>
    <view class="debug-toggle" @click="showDebug = !showDebug">
      <text class="debug-toggle-text">{{ showDebug ? '隐藏' : '显示' }}调试信息</text>
    </view>
  </view>
  <view class="page empty" v-else-if="!loading">加载失败</view>
  <view class="page empty" v-else>加载中...</view>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { getQuestion } from '@/api/questions.js'

import { API_BASE_URL } from '@/config.js'

const q = ref(null)
const loading = ref(true)
const imageFullUrl = ref('')
const showDebug = ref(false)

watch(() => q.value?.image_url, (url) => {
  if (!url || typeof url !== 'string') {
    imageFullUrl.value = ''
    return
  }
  const base = (API_BASE_URL || '').replace(/\/$/, '')
  imageFullUrl.value = url.startsWith('http') ? url : `${base}${url.startsWith('/') ? url : '/' + url}`
  // 调试：控制台输出，便于在微信开发者工具 / vConsole 中查看
  console.log('[错题详情] image_url from API:', url)
  console.log('[错题详情] API_BASE_URL:', API_BASE_URL)
  console.log('[错题详情] imageFullUrl:', imageFullUrl.value)
}, { immediate: true })

function onImageError(e) {
  console.warn('[错题详情] 图片加载失败', imageFullUrl.value, e)
  imageFullUrl.value = ''
}

function copyImageUrl() {
  if (!imageFullUrl.value) return
  uni.setClipboardData({
    data: imageFullUrl.value,
    success: () => uni.showToast({ title: '已复制到剪贴板', icon: 'none' })
  })
}

onMounted(async () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1]
  const id = parseInt((page.options || {}).id, 10)
  if (!id) { loading.value = false; return }
  try {
    q.value = await getQuestion(id)
  } catch (e) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page { padding: 24rpx; }
.card { background: #fff; border-radius: 12rpx; padding: 28rpx; margin-bottom: 24rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06); }
.label { display: block; font-size: 26rpx; color: #999; margin-bottom: 12rpx; }
.content { font-size: 30rpx; color: #333; white-space: pre-wrap; word-break: break-all; }
.img { width: 100%; border-radius: 8rpx; }
.meta { font-size: 24rpx; color: #999; }
.empty { text-align: center; padding: 60rpx; }
.img-placeholder { padding: 48rpx; text-align: center; color: #999; font-size: 28rpx; background: #f5f5f5; border-radius: 8rpx; }
.debug-card { background: #fffbe6; }
.debug-url { font-size: 24rpx; color: #666; word-break: break-all; display: block; margin-top: 8rpx; }
.debug-hint { font-size: 22rpx; color: #999; display: block; margin-top: 12rpx; }
.debug-toggle { padding: 16rpx; text-align: center; }
.debug-toggle-text { font-size: 24rpx; color: #999; }
</style>
