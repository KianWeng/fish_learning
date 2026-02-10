<template>
  <view class="page">
    <view class="progress">第 {{ currentIndex + 1 }} / {{ list.length }}</view>
    <view class="card" v-if="current">
      <view class="content">{{ current.content }}</view>
      <view class="actions" v-if="!showAnswer">
        <button class="btn" @click="showAnswer = true">查看解析与答案</button>
      </view>
      <template v-else>
        <view class="summary-block" v-if="current.summary">
          <text class="label">知识点·易错点</text>
          <text class="summary-text">{{ current.summary }}</text>
        </view>
        <view class="analysis" v-if="current.analysis">
          <text class="label">解析</text>
          <text class="text">{{ current.analysis }}</text>
        </view>
        <view class="answer" v-if="current.answer">
          <text class="label">答案</text>
          <text class="text">{{ current.answer }}</text>
        </view>
        <view class="rating">
          <text class="label">掌握程度</text>
          <view class="btns">
            <button class="btn forget" @click="submit('forget')">忘记</button>
            <button class="btn vague" @click="submit('vague')">模糊</button>
            <button class="btn remember" @click="submit('remember')">记得</button>
          </view>
        </view>
      </template>
    </view>
    <view class="empty" v-else-if="!loading">加载失败</view>
    <view class="empty" v-else>加载中...</view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getQuestion } from '@/api/questions.js'
import { submitReviewResult } from '@/api/reviews.js'

const ids = ref([])
const list = ref([])
const currentIndex = ref(0)
const showAnswer = ref(false)
const loading = ref(true)

const current = computed(() => list.value[currentIndex.value] || null)

onMounted(async () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1]
  const q = page.options || {}
  const idStr = q.ids || q.id
  if (!idStr) { loading.value = false; return }
  ids.value = idStr.split(',').map(s => parseInt(s, 10)).filter(Boolean)
  loading.value = true
  try {
    list.value = await Promise.all(ids.value.map(id => getQuestion(id)))
  } catch (e) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
})

async function submit(rating) {
  if (!current.value) return
  try {
    await submitReviewResult(current.value.id, rating)
    if (currentIndex.value < list.value.length - 1) {
      currentIndex.value++
      showAnswer.value = false
    } else {
      uni.showToast({ title: '复习完成' })
      setTimeout(() => uni.navigateBack(), 800)
    }
  } catch (e) {
    uni.showToast({ title: e.message || '提交失败', icon: 'none' })
  }
}
</script>

<style scoped>
.page { padding: 32rpx; background: var(--bg-page); min-height: 100vh; }
.progress { font-size: 26rpx; color: var(--text-hint); margin-bottom: 24rpx; }
.card { background: var(--bg-card); border-radius: 24rpx; padding: 32rpx; box-shadow: var(--shadow-card); }
.content { font-size: 30rpx; color: var(--text); white-space: pre-wrap; margin-bottom: 24rpx; }
.actions { margin-top: 24rpx; }
.btn { margin-top: 16rpx; padding: 24rpx; border-radius: 24rpx; font-size: 28rpx; }
.btn.forget { background: #ffebe9; color: #ee0a24; border: none; }
.btn.vague { background: #fff7e6; color: var(--warn); border: none; }
.btn.remember { background: var(--primary-bg); color: var(--success); border: none; }
.summary-block { margin-top: 24rpx; padding: 20rpx; background: linear-gradient(135deg, #e8f5e9 0%, #fff8e1 100%); border-radius: 12rpx; border-left: 6rpx solid #2e7d32; }
.summary-text { font-size: 28rpx; color: #2e7d32; white-space: pre-wrap; }
.analysis, .answer, .rating { margin-top: 24rpx; }
.label { display: block; font-size: 26rpx; color: var(--text-hint); margin-bottom: 8rpx; }
.text { font-size: 28rpx; color: var(--text); white-space: pre-wrap; }
.btns { display: flex; gap: 16rpx; margin-top: 12rpx; flex-wrap: wrap; }
.btns .btn { margin-top: 0; flex: 1; min-width: 120rpx; }
.empty { padding: 80rpx; text-align: center; color: var(--text-hint); font-size: 28rpx; }
</style>
