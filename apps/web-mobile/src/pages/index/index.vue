<template>
  <view class="page">
    <!-- 复习题目卡片 -->
    <view class="card question-card" v-if="todayQuestion">
      <view class="tag">题目 #{{ todayQuestion.id }}</view>
      <view class="q-body">
        <view class="q-placeholder" v-if="!showAnswer">
          <text class="q-title">复习题目</text>
          <text class="q-hint">点击查看答案或解析</text>
        </view>
        <view class="q-content" v-else>
          <text class="content-text">{{ todayQuestion.content }}</text>
          <view class="analysis" v-if="todayQuestion.analysis">
            <text class="label">解析</text>
            <text class="text">{{ todayQuestion.analysis }}</text>
          </view>
          <view class="answer" v-if="todayQuestion.answer">
            <text class="label">答案</text>
            <text class="text">{{ todayQuestion.answer }}</text>
          </view>
        </view>
        <button class="btn-show" @click="showAnswer = !showAnswer">
          {{ showAnswer ? '点击隐藏' : '点击显示' }}
        </button>
      </view>
    </view>
    <view class="card question-card empty-q" v-else-if="!loading">
      <text class="empty-text">今日暂无待复习</text>
      <text class="link" @click="onAddTap">去添加错题</text>
    </view>

    <!-- 快捷访问 -->
    <view class="section">
      <text class="section-title">快捷访问</text>
      <view class="quick-grid">
        <view class="quick-card" v-for="s in subjects.slice(0, 3)" :key="s.id" @click="goQuestions(s)">
          <view class="quick-icon">📖</view>
          <text class="quick-name">{{ s.name }}</text>
          <text class="quick-desc">查看错题</text>
        </view>
        <view class="quick-card add-card" @click="onAddTap">
          <view class="quick-icon add-icon">+</view>
          <text class="quick-name">新建</text>
        </view>
      </view>
    </view>

    <!-- 数据卡片 -->
    <view class="section">
      <view class="stats-row">
        <view class="stat-card">
          <text class="stat-icon">✓</text>
          <text class="stat-label">已解决</text>
          <text class="stat-value">{{ todayCount }}</text>
          <text class="stat-desc">今日待复习</text>
        </view>
        <view class="stat-card">
          <text class="stat-icon clock">⏱</text>
          <text class="stat-label">专注</text>
          <text class="stat-value">{{ studyMinutes }}m</text>
          <text class="stat-desc">学习时长</text>
        </view>
      </view>
    </view>

    <view class="tabbar-placeholder" />
    <TabBar current="index" />
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import TabBar from '@/components/TabBar.vue'
import { getTodayReviews } from '@/api/reviews.js'
import { listSubjects } from '@/api/subjects.js'

const todayQuestion = ref(null)
const showAnswer = ref(false)
const loading = ref(true)
const subjects = ref([])
const todayCount = ref(0)
const studyMinutes = ref(0)

async function load() {
  loading.value = true
  try {
    const [reviews, subj] = await Promise.all([getTodayReviews(), listSubjects()])
    subjects.value = subj || []
    todayCount.value = reviews.length
    todayQuestion.value = reviews[0] || null
    studyMinutes.value = 0
  } catch (e) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function goQuestions(s) {
  uni.navigateTo({ url: `/pages/questions/list?subject_id=${s.id}` })
}

/** 添加：新建错题本 或 拍照添加题目 */
function onAddTap() {
  uni.showActionSheet({
    itemList: ['新建错题本', '拍照添加题目'],
    success: (res) => {
      if (res.tapIndex === 0) {
        uni.navigateTo({ url: '/pages/subjects/create-with-photo' })
      } else if (res.tapIndex === 1) {
        uni.reLaunch({ url: '/pages/questions/list?openCamera=1' })
      }
    }
  })
}

onMounted(load)
</script>

<style scoped>
.page { padding: 24rpx 24rpx 140rpx; background: #f5f6fa; min-height: 100vh; }
.card { background: #fff; border-radius: 24rpx; padding: 32rpx; margin-bottom: 24rpx; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.06); }
.question-card .tag { display: inline-block; background: #1989fa; color: #fff; font-size: 24rpx; padding: 8rpx 20rpx; border-radius: 20rpx; margin-bottom: 20rpx; }
.q-body { min-height: 160rpx; }
.q-placeholder { text-align: center; padding: 24rpx 0; }
.q-title { display: block; font-size: 34rpx; font-weight: 600; color: #333; }
.q-hint { display: block; font-size: 26rpx; color: #999; margin-top: 12rpx; }
.content-text { font-size: 28rpx; color: #333; white-space: pre-wrap; display: block; margin-bottom: 20rpx; }
.analysis, .answer { margin-top: 20rpx; }
.label { display: block; font-size: 24rpx; color: #999; margin-bottom: 8rpx; }
.text { font-size: 26rpx; color: #555; white-space: pre-wrap; }
.btn-show { width: 100%; margin-top: 24rpx; height: 80rpx; line-height: 80rpx; background: #1989fa; color: #fff; border: none; border-radius: 16rpx; font-size: 28rpx; }
.empty-q { text-align: center; }
.empty-text { color: #999; font-size: 28rpx; }
.link { display: block; margin-top: 16rpx; color: #1989fa; font-size: 28rpx; }
.section { margin-bottom: 24rpx; }
.section-title { font-size: 30rpx; font-weight: 600; color: #333; margin-bottom: 20rpx; display: block; }
.quick-grid { display: flex; flex-wrap: wrap; gap: 20rpx; }
.quick-card { width: calc(50% - 10rpx); background: #e8f4ff; border-radius: 20rpx; padding: 28rpx; box-sizing: border-box; }
.quick-card.add-card { background: #fff; border: 2rpx dashed #ddd; }
.quick-icon { font-size: 48rpx; margin-bottom: 12rpx; }
.add-icon { font-size: 56rpx; color: #999; }
.quick-name { display: block; font-size: 28rpx; font-weight: 500; color: #333; }
.quick-desc { font-size: 24rpx; color: #1989fa; margin-top: 4rpx; }
.stats-row { display: flex; gap: 20rpx; }
.stat-card { flex: 1; background: #fff; border-radius: 20rpx; padding: 28rpx; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.06); }
.stat-icon { font-size: 36rpx; color: #07c160; }
.stat-icon.clock { color: #1989fa; }
.stat-label { display: block; font-size: 26rpx; color: #666; margin-top: 8rpx; }
.stat-value { display: block; font-size: 44rpx; font-weight: 600; color: #333; margin-top: 8rpx; }
.stat-desc { font-size: 24rpx; color: #999; margin-top: 4rpx; }
.tabbar-placeholder { height: 120rpx; }
</style>
