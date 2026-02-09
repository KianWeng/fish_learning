<template>
  <view class="page">
    <view class="header">
      <text class="title">{{ chapterName }}</text>
      <text class="sub" v-if="list.length">共 {{ list.length }} 道错题</text>
    </view>
    <view class="list" v-if="list.length">
      <view
        class="item-wrap"
        v-for="q in list"
        :key="q.id"
        @touchstart="onTouchStart($event, q)"
        @touchmove="onTouchMove($event, q)"
        @touchend="onTouchEnd"
      >
        <view class="item-delete" @click.stop="onDelete(q)">删除</view>
        <view
          class="item-slide"
          :style="{ transform: openId === q.id ? 'translateX(-120rpx)' : 'translateX(0)' }"
          @click="onItemClick(q)"
        >
          <view class="item-main">
            <text class="content">{{ q.content }}</text>
            <text class="time">{{ q.created_at }}</text>
          </view>
        </view>
      </view>
    </view>
    <view class="empty" v-else-if="!loading">
      <text class="empty-text">该章节暂无错题</text>
      <text class="empty-hint">点击右下角 + 添加错题</text>
    </view>
    <view class="empty" v-else>加载中...</view>

    <view class="float-btn" @click="onAddTap">+</view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { listQuestions, deleteQuestion } from '@/api/questions.js'
import { setSourcePath, getResultPath } from '@/utils/crop-store.js'

const subjectId = ref(0)
const chapterId = ref(0)
const subjectName = ref('')
const chapterName = ref('')
const list = ref([])
const loading = ref(true)
const openId = ref(null)
let touchStartX = 0

function onTouchStart(e, q) {
  touchStartX = e.touches[0].clientX
}

function onTouchMove(e, q) {
  const x = e.touches[0].clientX
  const delta = x - touchStartX
  if (delta < -40) openId.value = q.id
  else if (delta > 40) openId.value = null
}

function onTouchEnd() {}

function onItemClick(q) {
  if (openId.value === q.id) {
    openId.value = null
    return
  }
  goDetail(q.id)
}

async function onDelete(q) {
  const ok = await new Promise(r =>
    uni.showModal({
      title: '确认删除',
      content: '删除这道错题？',
      success: res => r(res.confirm)
    })
  )
  if (!ok) return
  try {
    await deleteQuestion(q.id)
    list.value = list.value.filter(x => x.id !== q.id)
    openId.value = null
    uni.showToast({ title: '已删除' })
  } catch (e) {
    uni.showToast({ title: e.message || '删除失败', icon: 'none' })
  }
}

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
  openId.value = null
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

/** 点击添加：新建章节目录 或 拍照添加题目 */
function onAddTap() {
  uni.showActionSheet({
    itemList: ['新建章节目录', '拍照添加题目'],
    success: (res) => {
      if (res.tapIndex === 0) goNewChapter()
      else if (res.tapIndex === 1) openCameraThenCrop()
    }
  })
}

function goNewChapter() {
  uni.navigateTo({
    url: `/pages/chapters/edit?subject_id=${subjectId.value}&subject_name=${encodeURIComponent(subjectName.value)}`
  })
}

function goAdd() {
  openCameraThenCrop()
}

function addPageUrl() {
  return `/pages/questions/add?subject_id=${subjectId.value}&chapter_id=${chapterId.value}&subject_name=${encodeURIComponent(subjectName.value)}&chapter_name=${encodeURIComponent(chapterName.value)}`
}

function initFromOptions(opts) {
  if (!opts) {
    const pages = getCurrentPages()
    const page = pages[pages.length - 1]
    opts = page.options || {}
  }
  subjectId.value = parseInt(opts.subject_id, 10) || 0
  chapterId.value = parseInt(opts.chapter_id, 10) || 0
  subjectName.value = opts.subject_name ? decodeURIComponent(opts.subject_name) : ''
  chapterName.value = opts.chapter_name ? decodeURIComponent(opts.chapter_name) : ''
  uni.setNavigationBarTitle({ title: chapterName.value || '' })
}

onLoad((opts) => {
  initFromOptions(opts)
})

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
.item-wrap {
  position: relative;
  border-radius: 16rpx;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.06);
}
.item-slide {
  position: relative;
  z-index: 1;
  width: 100%;
  padding: 28rpx 24rpx;
  background: #fff;
  transition: transform 0.2s ease;
  min-height: 100rpx;
  box-sizing: border-box;
}
/* 右侧固定一块白色遮罩盖住删除区，未滑动时不透红；左滑时随整块左移露出删除 */
.item-slide::after {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 120rpx;
  background: #fff;
  z-index: 0;
}
.item-main { position: relative; z-index: 1; min-width: 0; }
.content { font-size: 28rpx; color: #333; display: block; line-height: 1.4; }
.time { font-size: 24rpx; color: #999; margin-top: 12rpx; display: block; }
.item-delete {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 120rpx;
  background: #ee0a24;
  color: #fff;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  outline: none;
  box-shadow: none;
  -webkit-tap-highlight-color: transparent;
}
.item-delete::after { border: none; }
/* 删除按钮稍向内缩并做圆角，避免贴住最外圆角透红 */
.item-delete {
  right: 2rpx;
  width: 118rpx;
  border-radius: 0 14rpx 14rpx 0;
}
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
