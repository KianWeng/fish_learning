<template>
  <view class="page">
    <view class="header">
      <text class="title">{{ chapterName }}</text>
      <text class="sub" v-if="list.length">共 {{ list.length }} 道错题</text>
    </view>
    <view class="list" v-if="list.length">
      <view class="item" v-for="q in list" :key="q.id" @click="goDetail(q.id)">
        <text class="content">{{ q.content }}</text>
        <text class="time">{{ q.created_at }}</text>
      </view>
    </view>
    <view class="empty" v-else-if="!loading">
      <text class="empty-text">该章节暂无错题</text>
      <text class="empty-hint">点击右下角 + 添加错题</text>
    </view>
    <view class="empty" v-else>加载中...</view>

    <view class="float-btn" @click="goAdd">+</view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { listQuestions } from '@/api/questions.js'
import { setSourcePath, getResultPath } from '@/utils/crop-store.js'

const subjectId = ref(0)
const chapterId = ref(0)
const subjectName = ref('')
const chapterName = ref('')
const list = ref([])
const loading = ref(true)

async function load() {
  if (!subjectId.value || !chapterId.value) return
  loading.value = true
  try {
    list.value = await listQuestions({ subject_id: subjectId.value, chapter_id: chapterId.value })
  } catch (e) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function goDetail(id) {
  uni.navigateTo({ url: `/pages/questions/detail?id=${id}` })
}

function openCameraThenCrop() {
  uni.chooseImage({
    count: 1,
    sourceType: ['camera'],
    success: (res) => {
      setSourcePath(res.tempFilePaths[0])
      uni.navigateTo({ url: '/pages/common/image-crop' })
    }
  })
}

function goAdd() {
  openCameraThenCrop()
}

function addPageUrl() {
  return `/pages/questions/add?subject_id=${subjectId.value}&chapter_id=${chapterId.value}&subject_name=${encodeURIComponent(subjectName.value)}&chapter_name=${encodeURIComponent(chapterName.value)}`
}

function initFromOptions() {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1]
  const opts = page.options || {}
  subjectId.value = parseInt(opts.subject_id, 10) || 0
  chapterId.value = parseInt(opts.chapter_id, 10) || 0
  subjectName.value = opts.subject_name ? decodeURIComponent(opts.subject_name) : ''
  chapterName.value = opts.chapter_name ? decodeURIComponent(opts.chapter_name) : ''
  uni.setNavigationBarTitle({ title: chapterName.value || '章节错题' })
}

onMounted(() => {
  initFromOptions()
  load()
})

onShow(() => {
  initFromOptions()
  load()
  if (getResultPath()) {
    uni.navigateTo({ url: addPageUrl() })
  }
})
</script>

<style scoped>
.page { padding: 24rpx 24rpx 140rpx; background: #f5f6fa; min-height: 100vh; }
.header { padding: 20rpx 0 24rpx; }
.title { font-size: 36rpx; font-weight: 600; color: #1a1a2e; display: block; }
.sub { font-size: 26rpx; color: #6b7280; margin-top: 8rpx; display: block; }
.list { display: flex; flex-direction: column; gap: 16rpx; }
.item {
  padding: 28rpx;
  background: #fff;
  border-radius: 16rpx;
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06);
}
.content { font-size: 28rpx; color: #333; display: block; }
.time { font-size: 24rpx; color: #999; margin-top: 12rpx; display: block; }
.empty { padding: 80rpx 32rpx; text-align: center; }
.empty-text { display: block; color: #6b7280; font-size: 30rpx; }
.empty-hint { display: block; margin-top: 16rpx; color: #9ca3af; font-size: 26rpx; }
.float-btn {
  position: fixed;
  right: 32rpx;
  bottom: 120rpx;
  width: 96rpx;
  height: 96rpx;
  background: linear-gradient(135deg, #1989fa 0%, #0d6ef5 100%);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48rpx;
  box-shadow: 0 8rpx 24rpx rgba(25,137,250,0.35);
  z-index: 10;
}
</style>
