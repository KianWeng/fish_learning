<template>
  <view class="page">
    <view v-if="list.length === 0 && !loading" class="empty">今日暂无待复习题目</view>
    <view v-else-if="list.length === 0" class="empty">加载中...</view>
    <view v-else>
      <view class="progress">第 {{ currentIndex + 1 }} / {{ list.length }}</view>
      <view class="card" v-if="current">
        <view class="content">{{ current.content }}</view>
        <view class="actions" v-if="!showAnswer">
          <button class="btn" @click="showAnswer = true">查看解析与答案</button>
        </view>
        <template v-else>
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
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getTodayReviews, submitReviewResult } from '@/api/reviews.js'

const list = ref([])
const currentIndex = ref(0)
const showAnswer = ref(false)
const loading = ref(true)

const current = computed(() => list.value[currentIndex.value] || null)

async function load() {
  loading.value = true
  try {
    list.value = await getTodayReviews()
  } catch (e) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function submit(rating) {
  if (!current.value) return
  try {
    await submitReviewResult(current.value.id, rating)
    list.value = list.value.filter((q) => q.id !== current.value.id)
    if (list.value.length === 0) {
      currentIndex.value = 0
      return
    }
    if (currentIndex.value >= list.value.length) currentIndex.value = list.value.length - 1
    showAnswer.value = false
  } catch (e) {
    uni.showToast({ title: e.message || '提交失败', icon: 'none' })
  }
}

onMounted(load)
</script>

<style scoped>
.page { padding: 24rpx; }
.progress { font-size: 26rpx; color: #999; margin-bottom: 24rpx; }
.card { background: #fff; border-radius: 12rpx; padding: 32rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06); }
.content { font-size: 30rpx; color: #333; white-space: pre-wrap; margin-bottom: 24rpx; }
.actions { margin-top: 24rpx; }
.btn { margin-top: 16rpx; padding: 24rpx; border-radius: 12rpx; font-size: 28rpx; }
.btn.forget { background: #ffebe9; color: #ee0a24; border: none; }
.btn.vague { background: #fff7e6; color: #fa8c16; border: none; }
.btn.remember { background: #e6f7ff; color: #07c160; border: none; }
.analysis, .answer, .rating { margin-top: 24rpx; }
.label { display: block; font-size: 26rpx; color: #999; margin-bottom: 8rpx; }
.text { font-size: 28rpx; color: #333; white-space: pre-wrap; }
.btns { display: flex; gap: 16rpx; margin-top: 12rpx; flex-wrap: wrap; }
.btns .btn { margin-top: 0; flex: 1; min-width: 120rpx; }
.empty { padding: 80rpx; text-align: center; color: #999; font-size: 28rpx; }
</style>
