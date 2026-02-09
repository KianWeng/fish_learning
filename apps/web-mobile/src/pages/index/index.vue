<template>
  <view class="page">
    <!-- 复习题目卡片 -->
    <view class="card question-card" v-if="todayQuestion">
      <view class="card-head">
        <view class="tag">题目 #{{ todayQuestion.id }}</view>
      </view>
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
        <button class="btn-show" :class="{ active: showAnswer }" @click="showAnswer = !showAnswer">
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
        <view
          class="quick-card quick-card-subject"
          v-for="s in subjects.slice(0, 3)"
          :key="s.id"
          @click="goQuestions(s)"
        >
          <view class="quick-cover">
            <CachedImage img-class="quick-cover-img" :src="getSubjectCoverUrl(s)" mode="aspectFill" img-style="width: 100%; height: 100%; display: block;" />
          </view>
          <view class="quick-cover-overlay"></view>
          <view class="quick-content">
            <text class="quick-name">{{ s.name }}</text>
            <text class="quick-desc">查看错题</text>
          </view>
        </view>
        <view class="quick-card add-card" @click="onAddTap">
          <view class="quick-icon-wrap add-icon-wrap">
            <text class="add-plus">+</text>
          </view>
          <text class="quick-name">新建</text>
        </view>
      </view>
    </view>

    <!-- 数据卡片 -->
    <view class="section">
      <view class="stats-row">
        <view class="stat-card">
          <view class="stat-icon-wrap">
            <text class="stat-icon">✓</text>
          </view>
          <text class="stat-label">已解决</text>
          <text class="stat-value">{{ todayCount }}</text>
          <text class="stat-desc">今日待复习</text>
        </view>
        <view class="stat-card">
          <view class="stat-icon-wrap clock">
            <text class="stat-icon">⏱</text>
          </view>
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
import CachedImage from '@/components/CachedImage.vue'
import { getTodayReviews } from '@/api/reviews.js'
import { listSubjects } from '@/api/subjects.js'
import { getSubjectCoverUrl } from '@/utils/cover.js'

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

/** 进入该错题本的内容页（章节列表） */
function goQuestions(s) {
  uni.navigateTo({
    url: `/pages/chapters/list?subject_id=${s.id}&subject_name=${encodeURIComponent(s.name || '')}`
  })
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
/* 设计令牌：柔和主色 + 功能区分色 */
.page {
  --primary: #4A90E2;
  --primary-light: #66B2FF;
  --primary-bg: #E3F2FD;
  --success: #A5D6A7;
  --warn: #FFCC80;
  --text: #333;
  --text-secondary: #666;
  --text-hint: #999;
  --bg-page: #F5F5F5;
  --bg-card: #fff;
  --shadow: 0 2rpx 16rpx rgba(0,0,0,0.05);
}

.page {
  padding: 32rpx 32rpx 160rpx;
  background: var(--bg-page);
  min-height: 100vh;
}

.card {
  background: var(--bg-card);
  border-radius: 24rpx;
  padding: 24rpx;
  margin-bottom: 32rpx;
  box-shadow: var(--shadow);
}

.question-card {
  position: relative;
}
.card-head {
  margin-bottom: 16rpx;
}
.question-card .tag {
  display: inline-block;
  background: var(--primary);
  color: #fff;
  font-size: 22rpx;
  padding: 8rpx 20rpx;
  border-radius: 12rpx;
}
.q-body { min-height: 140rpx; }
.q-placeholder { text-align: center; padding: 20rpx 0; }
.q-title {
  display: block;
  font-size: 36rpx;
  font-weight: 700;
  color: var(--primary);
}
.q-hint {
  display: block;
  font-size: 24rpx;
  color: var(--text-hint);
  margin-top: 12rpx;
}
.content-text {
  font-size: 28rpx;
  color: var(--text);
  white-space: pre-wrap;
  display: block;
  margin-bottom: 20rpx;
}
.analysis, .answer { margin-top: 20rpx; }
.label { display: block; font-size: 24rpx; color: var(--text-hint); margin-bottom: 8rpx; }
.text { font-size: 26rpx; color: var(--text-secondary); white-space: pre-wrap; }

.btn-show {
  width: 100%;
  margin-top: 24rpx;
  height: 80rpx;
  line-height: 80rpx;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 24rpx;
  font-size: 28rpx;
  transition: background 0.2s;
}
.btn-show:active { background: var(--primary-light); }

.empty-q { text-align: center; }
.empty-text { color: var(--text-hint); font-size: 28rpx; }
.link { display: block; margin-top: 16rpx; color: var(--primary); font-size: 28rpx; }

.section { margin-bottom: 32rpx; }
.section-title {
  font-size: 32rpx;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 24rpx;
  display: block;
}

.quick-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
}
.quick-card {
  width: calc(33.333% - 14rpx);
  border-radius: 24rpx;
  padding: 24rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  position: relative;
  overflow: hidden;
  min-height: 180rpx;
}
.quick-card-subject {
  background: none !important;
  justify-content: flex-end;
}
.quick-card-subject .quick-cover {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
}
.quick-card-subject .quick-cover-img {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  width: 100% !important;
  height: 100% !important;
  display: block;
}
.quick-card-subject .quick-cover-overlay {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.5) 100%);
}
.quick-card-subject .quick-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 100%;
}
.quick-card-subject .quick-icon { color: #fff; }
.quick-card-subject .quick-name { color: #fff; text-shadow: 0 1rpx 4rpx rgba(0,0,0,0.4); }
.quick-card-subject .quick-desc { color: rgba(255,255,255,0.9); }
.quick-card.add-card {
  background: transparent;
  border: 2rpx dashed var(--primary);
}
.quick-icon-wrap {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12rpx;
}
.quick-icon {
  font-size: 40rpx;
  font-weight: 600;
  color: var(--primary);
}
.add-icon-wrap {
  border: 2rpx solid var(--primary);
  border-radius: 50%;
}
.add-plus {
  font-size: 44rpx;
  color: var(--primary);
  font-weight: 300;
  line-height: 1;
}
.quick-name {
  display: block;
  font-size: 26rpx;
  font-weight: 500;
  color: var(--text);
}
.quick-desc {
  font-size: 22rpx;
  color: var(--text-secondary);
  margin-top: 4rpx;
}

.stats-row { display: flex; gap: 24rpx; }
.stat-card {
  flex: 1;
  background: var(--bg-page);
  border-radius: 24rpx;
  padding: 24rpx;
  box-shadow: var(--shadow);
}
.stat-icon-wrap {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2rpx solid var(--primary);
  border-radius: 50%;
  margin-bottom: 12rpx;
}
.stat-icon {
  font-size: 28rpx;
  color: var(--primary);
  font-weight: 700;
}
.stat-icon-wrap.clock .stat-icon { color: var(--primary); }
.stat-label {
  display: block;
  font-size: 26rpx;
  font-weight: 600;
  color: var(--primary);
}
.stat-value {
  display: block;
  font-size: 48rpx;
  font-weight: 700;
  color: var(--primary);
  margin-top: 8rpx;
}
.stat-desc {
  font-size: 22rpx;
  color: var(--text-hint);
  margin-top: 4rpx;
}

.tabbar-placeholder { height: 120rpx; }
</style>
