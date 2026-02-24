<template>
  <view class="page">
    <view class="header-row">
      <text class="header-title">全部错题</text>
      <picker mode="selector" :range="courseFilterOptions" range-key="label" :value="courseFilterIndex" @change="onCourseFilterChange">
        <view class="header-filter">
          <text>{{ courseFilterOptions[courseFilterIndex]?.label || '全部' }}</text>
          <text class="header-filter-arrow">▼</text>
        </view>
      </picker>
    </view>
    <view class="list" v-if="list.length">
      <view class="item" v-for="s in list" :key="s.id">
        <view class="item-left">
          <text class="name">{{ s.name }}</text>
          <text class="course-tag" v-if="s.course">{{ s.course }}</text>
        </view>
        <view class="actions">
          <text class="link" @click="goChapters(s)">章节</text>
          <text class="link" @click="goEdit(s)">编辑</text>
          <text class="link danger" @click="onDelete(s)">删除</text>
        </view>
      </view>
    </view>
    <view class="empty" v-else-if="!loading">暂无错题本，点击右下角 + 添加</view>
    <view class="empty" v-else>加载中...</view>

    <view class="float-btn" @click="onAddTap">+</view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { listSubjects, deleteSubject } from '@/api/subjects.js'
import { setSourcePath, getResultPath } from '@/utils/crop-store.js'
import { COMMON_COURSES } from '@/utils/course.js'

const list = ref([])
const loading = ref(true)
/** 当前选中的科目筛选：空字符串表示「全部」 */
const selectedCourse = ref('')
const courseFilterOptions = ref([
  { label: '全部', value: '' },
  ...COMMON_COURSES.map((c) => ({ label: c, value: c }))
])
const courseFilterIndex = ref(0)

async function load() {
  loading.value = true
  const course = selectedCourse.value
  try {
    list.value = await listSubjects(course ? { course } : {})
    if (!course) {
      const customCourses = [...new Set(list.value.map((s) => s.course).filter(Boolean))]
        .filter((c) => !COMMON_COURSES.includes(c))
        .sort((a, b) => a.localeCompare(b))
      courseFilterOptions.value = [
        { label: '全部', value: '' },
        ...COMMON_COURSES.map((c) => ({ label: c, value: c })),
        ...customCourses.map((c) => ({ label: c, value: c }))
      ]
    }
  } catch (e) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
    list.value = []
  } finally {
    loading.value = false
  }
}

function onCourseFilterChange(e) {
  const idx = Number(e.detail.value)
  if (idx >= 0 && idx < courseFilterOptions.value.length) {
    courseFilterIndex.value = idx
    selectedCourse.value = courseFilterOptions.value[idx].value ?? ''
    load()
  }
}

/** 添加：新建错题本(科目)、拍照添加题目 或 手动添加题目 */
function onAddTap() {
  uni.showActionSheet({
    itemList: ['新建错题本', '拍照添加题目', '手动添加题目'],
    success: (res) => {
      if (res.tapIndex === 0) goAdd()
      else if (res.tapIndex === 1) openCameraThenCrop()
      else if (res.tapIndex === 2) uni.navigateTo({ url: '/pages/questions/add?mode=manual' })
    }
  })
}

function openCameraThenCrop() {
  uni.chooseImage({
    count: 1,
    sourceType: ['album', 'camera'],
    success: (res) => {
      setSourcePath(res.tempFilePaths[0])
      uni.navigateTo({ url: '/pages/common/image-crop' })
    }
  })
}

function goAdd() {
  uni.navigateTo({ url: '/pages/subjects/edit' })
}

function goEdit(s) {
  const course = s.course != null ? encodeURIComponent(s.course) : ''
  uni.navigateTo({ url: `/pages/subjects/edit?id=${s.id}&name=${encodeURIComponent(s.name)}&sort=${s.sort}&course=${course}` })
}

function goChapters(s) {
  uni.navigateTo({ url: `/pages/chapters/list?subject_id=${s.id}&subject_name=${encodeURIComponent(s.name)}` })
}

async function onDelete(s) {
  const ok = await new Promise(r => uni.showModal({ title: '确认删除', content: `删除科目「${s.name}」？`, success: res => r(res.confirm) }))
  if (!ok) return
  try {
    await deleteSubject(s.id)
    uni.showToast({ title: '已删除' })
    load()
  } catch (e) {
    uni.showToast({ title: e.message || '删除失败', icon: 'none' })
  }
}

onLoad(() => {
  uni.setNavigationBarTitle({ title: '科目管理' })
})

onShow(() => {
  if (getResultPath()) {
    uni.navigateTo({ url: '/pages/questions/add' })
    return
  }
  load()
})
</script>

<style scoped>
.page { padding: 32rpx 32rpx 140rpx; min-height: 100vh; background: var(--bg-page); }
.list { display: flex; flex-direction: column; gap: 16rpx; }
.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  margin-bottom: 24rpx;
  padding: 0 4rpx;
}
.header-title { font-size: 36rpx; font-weight: 600; color: var(--text); }
.header-filter {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 12rpx 24rpx;
  min-width: 120rpx;
  background: var(--primary-bg);
  border-radius: 12rpx;
  font-size: 26rpx;
  color: var(--primary);
  text-align: center;
}
.header-filter-arrow { font-size: 20rpx; color: var(--text-hint); }
.item {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;
  padding: 28rpx;
  background: var(--bg-card);
  border-radius: 24rpx;
  box-shadow: var(--shadow-card);
}
.item-left { display: flex; align-items: center; gap: 12rpx; flex: 1; min-width: 0; }
.item .name { font-size: 30rpx; font-weight: 500; color: var(--text); }
.course-tag { font-size: 22rpx; color: var(--text-hint); flex-shrink: 0; }
.item .actions { flex-shrink: 0; }
.actions { display: flex; gap: 24rpx; }
.link { font-size: 26rpx; color: var(--primary); }
.link.danger { color: #ee0a24; }
.empty { padding: 60rpx; text-align: center; color: var(--text-hint); font-size: 28rpx; }

.float-btn {
  position: fixed;
  right: 32rpx;
  bottom: 60rpx;
  width: 96rpx;
  height: 96rpx;
  background: linear-gradient(135deg, var(--primary) 0%, #3a7bc8 100%);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48rpx;
  box-shadow: 0 8rpx 24rpx rgba(74,144,226,0.35);
  z-index: 10;
}
</style>
