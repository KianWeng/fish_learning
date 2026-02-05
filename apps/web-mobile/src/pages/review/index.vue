<template>
  <view class="page">
    <view class="header">
      <text class="title">复习 ({{ selectedIds.length }})</text>
      <text class="right" @click="filterSubject = null">全部</text>
    </view>

    <!-- 汇总卡片 -->
    <view class="summary-row">
      <view class="summary-card">
        <text class="summary-value">{{ list.length }}</text>
        <text class="summary-label">总计</text>
      </view>
      <view class="summary-card active">
        <view class="dot" v-if="list.length > 0"></view>
        <text class="summary-value">{{ list.length }}</text>
        <text class="summary-label">待复习</text>
      </view>
      <view class="summary-card">
        <text class="summary-value">{{ masteryPercent }}%</text>
        <text class="summary-label">掌握度</text>
      </view>
    </view>

    <!-- 筛选 -->
    <view class="filter-bar">
      <view class="filter-btn">
        <text>排序: 急迫度</text>
      </view>
      <picker :range="subjectOptions" range-key="name" @change="onSubjectFilterChange">
        <view class="filter-btn">
          <text>科目: {{ subjectFilterName }}</text>
          <text class="arrow">▼</text>
        </view>
      </picker>
      <view class="filter-btn">
        <text>状态: 全部</text>
        <text class="arrow">▼</text>
      </view>
    </view>

    <!-- 列表 -->
    <view class="list" v-if="filteredList.length">
      <view class="list-item" v-for="q in filteredList" :key="q.id" @click="toggleSelect(q.id)">
        <view class="item-thumb"></view>
        <view class="item-main">
          <text class="item-subject">题目 #{{ q.id }}</text>
          <view class="item-action" @click.stop="goReviewOne(q)">
            <text class="action-dot">!</text>
            <text class="action-text">立即复习</text>
          </view>
        </view>
        <view class="item-check" :class="{ on: selectedIds.includes(q.id) }">
          {{ selectedIds.includes(q.id) ? '✓' : '' }}
        </view>
      </view>
    </view>
    <view class="empty" v-else-if="!loading">今日暂无待复习题目</view>
    <view class="empty" v-else>加载中...</view>

    <!-- 底部操作栏 -->
    <view class="bottom-bar" v-if="filteredList.length">
      <view class="bar-btn">移动</view>
      <view class="bar-btn">删除</view>
      <view class="bar-btn primary" @click="startReview">
        复习 ({{ selectedIds.length || filteredList.length }})
      </view>
    </view>

    <view class="tabbar-placeholder" />
    <TabBar current="review" />
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import TabBar from '@/components/TabBar.vue'
import { getTodayReviews, submitReviewResult } from '@/api/reviews.js'
import { listSubjects } from '@/api/subjects.js'

const list = ref([])
const loading = ref(true)
const selectedIds = ref([])
const filterSubject = ref(null)
const subjects = ref([])
const subjectOptions = ref([{ id: null, name: '全部' }])

const subjectFilterName = computed(() => {
  if (!filterSubject.value) return '全部'
  const s = subjects.value.find(x => x.id === filterSubject.value)
  return s ? s.name : '全部'
})

const filteredList = computed(() => {
  if (!filterSubject.value) return list.value
  return list.value.filter(q => q.subject_id === filterSubject.value)
})

const masteryPercent = computed(() => 0)

async function load() {
  loading.value = true
  try {
    const [reviews, subj] = await Promise.all([getTodayReviews(), listSubjects()])
    list.value = reviews
    subjects.value = subj || []
    subjectOptions.value = [{ id: null, name: '全部' }, ...subjects.value]
    selectedIds.value = reviews.map(q => q.id)
  } catch (e) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function toggleSelect(id) {
  const i = selectedIds.value.indexOf(id)
  if (i >= 0) selectedIds.value = selectedIds.value.filter(x => x !== id)
  else selectedIds.value = [...selectedIds.value, id]
}

function goReviewOne(q) {
  uni.navigateTo({ url: `/pages/review/do?ids=${q.id}` })
}

function onSubjectFilterChange(e) {
  const i = e.detail.value
  const opts = subjectOptions.value[i]
  filterSubject.value = opts && opts.id != null ? opts.id : null
}

function startReview() {
  const ids = selectedIds.value.length ? selectedIds.value : filteredList.value.map(q => q.id)
  if (!ids.length) return
  uni.navigateTo({ url: '/pages/review/do?ids=' + ids.join(',') })
}

onMounted(load)
</script>

<style scoped>
.page { padding: 24rpx 24rpx 180rpx; background: #f5f6fa; min-height: 100vh; }
.header { display: flex; align-items: center; justify-content: space-between; padding: 24rpx 0; }
.title { font-size: 40rpx; font-weight: 600; color: #333; }
.right { font-size: 28rpx; color: #1989fa; }
.summary-row { display: flex; gap: 20rpx; margin-bottom: 24rpx; }
.summary-card { flex: 1; background: #e8f4ff; border-radius: 20rpx; padding: 24rpx; text-align: center; position: relative; }
.summary-card.active { background: #1989fa; }
.summary-card.active .summary-value, .summary-card.active .summary-label { color: #fff; }
.dot { position: absolute; top: 16rpx; right: 16rpx; width: 16rpx; height: 16rpx; background: #ee0a24; border-radius: 50%; }
.summary-value { display: block; font-size: 40rpx; font-weight: 600; color: #333; }
.summary-label { font-size: 24rpx; color: #666; margin-top: 4rpx; }
.filter-bar { display: flex; gap: 16rpx; margin-bottom: 24rpx; flex-wrap: wrap; }
.filter-btn { display: flex; align-items: center; gap: 8rpx; padding: 16rpx 24rpx; background: #fff; border-radius: 24rpx; font-size: 26rpx; color: #333; box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06); }
.arrow { font-size: 20rpx; color: #999; }
.list { display: flex; flex-direction: column; gap: 20rpx; }
.list-item { display: flex; align-items: center; gap: 24rpx; padding: 24rpx; background: #fff; border-radius: 20rpx; border: 2rpx solid #e8f4ff; box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.04); }
.item-thumb { width: 100rpx; height: 100rpx; background: #f0f0f0; border-radius: 12rpx; flex-shrink: 0; }
.item-main { flex: 1; min-width: 0; }
.item-subject { display: block; font-size: 28rpx; font-weight: 500; color: #333; }
.item-action { display: inline-flex; align-items: center; gap: 8rpx; margin-top: 8rpx; }
.action-dot { width: 28rpx; height: 28rpx; line-height: 28rpx; text-align: center; background: #ff4d4f; color: #fff; border-radius: 50%; font-size: 20rpx; }
.action-text { font-size: 24rpx; color: #ff4d4f; }
.item-check { width: 44rpx; height: 44rpx; border: 2rpx solid #1989fa; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 28rpx; color: #fff; flex-shrink: 0; }
.item-check.on { background: #1989fa; }
.empty { padding: 80rpx; text-align: center; color: #999; font-size: 28rpx; }
.bottom-bar { position: fixed; left: 0; right: 0; bottom: 120rpx; height: 100rpx; padding: 0 24rpx; background: #fff; display: flex; align-items: center; gap: 24rpx; box-shadow: 0 -4rpx 20rpx rgba(0,0,0,0.06); z-index: 10; padding-bottom: env(safe-area-inset-bottom); }
.bar-btn { flex: 1; text-align: center; font-size: 28rpx; color: #666; }
.bar-btn.primary { flex: 2; background: #1989fa; color: #fff; height: 72rpx; line-height: 72rpx; border-radius: 36rpx; }
.tabbar-placeholder { height: 120rpx; }
</style>
