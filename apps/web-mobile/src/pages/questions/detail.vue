<template>
  <view class="page" v-if="q">
    <view class="card" v-if="q.image_url">
      <image :src="imageFullUrl" mode="widthFix" class="img" />
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

watch(() => q.value?.image_url, (url) => {
  if (url) imageFullUrl.value = url.startsWith('http') ? url : API_BASE_URL + url
}, { immediate: true })

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
</style>
