<template>
  <view class="page">
    <view class="header">
      <text class="title">复习 ({{ selectedIds.length }})</text>
      <text class="right" @click="filterCourse = ''; courseFilterIndex = 0">全部</text>
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
      <picker mode="selector" :range="courseFilterOptions" range-key="label" :value="courseFilterIndex" @change="onCourseFilterChange">
        <view class="filter-btn">
          <text>科目: {{ courseFilterName }}</text>
          <text class="arrow">▼</text>
        </view>
      </picker>
      <picker mode="selector" :range="statusOptions" range-key="label" :value="statusIndex" @change="onStatusFilterChange">
        <view class="filter-btn">
          <text>状态: {{ statusOptions[statusIndex]?.label }}</text>
          <text class="arrow">▼</text>
        </view>
      </picker>
    </view>

    <!-- 列表 -->
    <view class="list" v-if="filteredList.length">
      <view class="list-item" v-for="q in filteredList" :key="q.id" @click="toggleSelect(q.id)">
        <view class="item-course-icon">
          <image class="course-icon-img" :src="courseIconUrl(q)" mode="aspectFit" />
        </view>
        <view class="item-main">
          <text class="item-subject">{{ q.subject_name || ('题目 #' + q.id) }}</text>
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
    <view class="empty" v-else-if="!loading">{{ statusOptions[statusIndex]?.label === '待复习' ? '今日暂无待复习题目' : '暂无题目' }}</view>
    <view class="empty" v-else>加载中...</view>

    <!-- 底部操作栏 -->
    <view class="bottom-bar" v-if="filteredList.length">
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
import { onShow } from '@dcloudio/uni-app'
import TabBar from '@/components/TabBar.vue'
import { getReviewList, getReviewStats } from '@/api/reviews.js'
import { getCourseIconDataUri } from '@/utils/course.js'
import { COMMON_COURSES } from '@/utils/course.js'

const list = ref([])
const loading = ref(true)
const selectedIds = ref([])
const filterCourse = ref('')
const courseFilterOptions = ref([
  { label: '全部', value: '' },
  ...COMMON_COURSES.map((c) => ({ label: c, value: c }))
])
const courseFilterIndex = ref(0)
const stats = ref({ total: 0, mastered: 0 })

const statusOptions = [
  { label: '全部', value: 'all' },
  { label: '待复习', value: 'today' },
  { label: '已排期', value: 'scheduled' },
  { label: '未开始', value: 'new' }
]
const statusIndex = ref(1)

const courseFilterName = computed(() => {
  const opts = courseFilterOptions.value[courseFilterIndex.value]
  return opts ? opts.label : '全部'
})

const filteredList = computed(() => {
  if (!filterCourse.value) return list.value
  return list.value.filter(q => (q.subject_course || '') === filterCourse.value)
})

/** 掌握度 = 已掌握题目数 ÷ 全部题目数 × 100 */
const masteryPercent = computed(() => {
  const total = stats.value.total || 0
  if (total === 0) return 0
  const mastered = stats.value.mastered || 0
  return Math.round((mastered / total) * 100)
})

async function load() {
  loading.value = true
  const status = statusOptions[statusIndex.value]?.value ?? 'today'
  try {
    const [reviews, reviewStats] = await Promise.all([
      getReviewList(status),
      getReviewStats().catch(() => ({ total: 0, mastered: 0 }))
    ])
    list.value = reviews || []
    selectedIds.value = list.value.map(q => q.id)
    stats.value = reviewStats || { total: 0, mastered: 0 }
    const customCourses = [...new Set(list.value.map((q) => q.subject_course).filter(Boolean))]
      .filter((c) => !COMMON_COURSES.includes(c))
      .sort((a, b) => a.localeCompare(b))
    courseFilterOptions.value = [
      { label: '全部', value: '' },
      ...COMMON_COURSES.map((c) => ({ label: c, value: c })),
      ...customCourses.map((c) => ({ label: c, value: c }))
    ]
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

function courseIconUrl(q) {
  return getCourseIconDataUri(q?.subject_course)
}

function onCourseFilterChange(e) {
  const i = Number(e.detail.value)
  if (i >= 0 && i < courseFilterOptions.value.length) {
    courseFilterIndex.value = i
    filterCourse.value = courseFilterOptions.value[i].value ?? ''
  }
}

function onStatusFilterChange(e) {
  statusIndex.value = Number(e.detail.value)
  load()
}

function startReview() {
  const ids = selectedIds.value.length ? selectedIds.value : filteredList.value.map(q => q.id)
  if (!ids.length) return
  uni.navigateTo({ url: '/pages/review/do?ids=' + ids.join(',') })
}

onMounted(load)
onShow(() => { load() })
</script>

<style scoped>
.page { padding: 32rpx 32rpx 180rpx; background: var(--bg-page); min-height: 100vh; }
.header { display: flex; align-items: center; justify-content: space-between; padding: 24rpx 0; }
.title { font-size: 40rpx; font-weight: 600; color: var(--text); }
.right { font-size: 28rpx; color: var(--primary); }
.summary-row { display: flex; gap: 24rpx; margin-bottom: 32rpx; }
.summary-card {
  flex: 1;
  background: var(--primary-bg);
  border-radius: 24rpx;
  padding: 24rpx;
  text-align: center;
  position: relative;
  box-shadow: var(--shadow);
}
.summary-card.active { background: var(--primary); }
.summary-card.active .summary-value, .summary-card.active .summary-label { color: #fff; }
.dot { position: absolute; top: 16rpx; right: 16rpx; width: 16rpx; height: 16rpx; background: var(--warn); border-radius: 50%; }
.summary-value { display: block; font-size: 40rpx; font-weight: 600; color: var(--text); }
.summary-label { font-size: 24rpx; color: var(--text-secondary); margin-top: 4rpx; }
.filter-bar { display: flex; gap: 16rpx; margin-bottom: 24rpx; flex-wrap: wrap; }
.filter-btn {
  display: flex; align-items: center; gap: 8rpx;
  padding: 16rpx 24rpx;
  background: var(--bg-card);
  border-radius: 24rpx;
  font-size: 26rpx; color: var(--text);
  box-shadow: var(--shadow);
}
.arrow { font-size: 20rpx; color: var(--text-hint); }
.list { display: flex; flex-direction: column; gap: 20rpx; }
.list-item {
  display: flex; align-items: center; gap: 20rpx;
  padding: 24rpx;
  background: var(--bg-card);
  border-radius: 24rpx;
  border: 2rpx solid var(--primary-bg);
  box-shadow: var(--shadow);
}
.item-course-icon {
  width: 56rpx; height: 56rpx;
  background: var(--primary-bg);
  border-radius: 12rpx;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.course-icon-img { width: 36rpx; height: 36rpx; }
.item-main { flex: 1; min-width: 0; }
.item-subject { display: block; font-size: 28rpx; font-weight: 500; color: var(--text); }
.item-action { display: inline-flex; align-items: center; gap: 8rpx; margin-top: 8rpx; }
.action-dot { width: 28rpx; height: 28rpx; line-height: 28rpx; text-align: center; background: var(--warn); color: #fff; border-radius: 50%; font-size: 20rpx; }
.action-text { font-size: 24rpx; color: var(--warn); }
.item-check {
  width: 44rpx; height: 44rpx;
  border: 2rpx solid var(--primary);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 28rpx; color: #fff;
  flex-shrink: 0;
}
.item-check.on { background: var(--primary); }
.empty { padding: 80rpx; text-align: center; color: var(--text-hint); font-size: 28rpx; }
.bottom-bar {
  position: fixed; left: 0; right: 0; bottom: 120rpx;
  height: 100rpx; padding: 0 24rpx;
  background: var(--bg-card);
  display: flex; align-items: center; gap: 24rpx;
  box-shadow: 0 -4rpx 20rpx rgba(0,0,0,0.06);
  z-index: 10;
  padding-bottom: env(safe-area-inset-bottom);
}
.bar-btn { flex: 1; text-align: center; font-size: 28rpx; color: var(--text-secondary); }
.bar-btn.primary { flex: 2; background: var(--primary); color: #fff; height: 72rpx; line-height: 72rpx; border-radius: 36rpx; }
.tabbar-placeholder { height: 120rpx; }
</style>
