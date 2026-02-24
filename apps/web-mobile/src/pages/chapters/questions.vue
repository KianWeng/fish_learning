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
      <text class="empty-text">{{ ungroupedOnly ? '暂无未分组错题' : '该章节暂无错题' }}</text>
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
const chapterId = ref(null)
const subjectName = ref('')
const chapterName = ref('')
const ungroupedOnly = ref(false)
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
  if (!subjectId.value) return
  if (!ungroupedOnly.value && (chapterId.value == null || chapterId.value === '')) return
  loading.value = true
  try {
    const params = { subject_id: subjectId.value }
    if (ungroupedOnly.value) params.ungrouped_only = true
    else params.chapter_id = chapterId.value
    list.value = await listQuestions(params)
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
    sourceType: ['album', 'camera'],
    success: (res) => {
      setSourcePath(res.tempFilePaths[0])
      uni.navigateTo({ url: '/pages/common/image-crop' })
    }
  })
}

/** 点击添加：新建章节目录、拍照添加题目 或 手动添加题目 */
function onAddTap() {
  uni.showActionSheet({
    itemList: ['新建章节目录', '拍照添加题目', '手动添加题目'],
    success: (res) => {
      if (res.tapIndex === 0) goNewChapter()
      else if (res.tapIndex === 1) openCameraThenCrop()
      else if (res.tapIndex === 2) goManualAdd()
    }
  })
}

function goManualAdd() {
  const base = addPageUrl()
  uni.navigateTo({ url: base + (base.includes('?') ? '&' : '?') + 'mode=manual' })
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
  const base = `subject_id=${subjectId.value}&subject_name=${encodeURIComponent(subjectName.value)}`
  return `/pages/questions/add?${base}${ungroupedOnly.value ? '' : `&chapter_id=${chapterId.value}&chapter_name=${encodeURIComponent(chapterName.value)}`}`
}

function initFromOptions(opts) {
  if (!opts) {
    const pages = getCurrentPages()
    const page = pages[pages.length - 1]
    opts = page.options || {}
  }
  subjectId.value = parseInt(opts.subject_id, 10) || 0
  ungroupedOnly.value = opts.ungrouped_only === '1' || opts.ungrouped_only === true
  chapterId.value = ungroupedOnly.value ? null : (parseInt(opts.chapter_id, 10) || 0)
  subjectName.value = opts.subject_name ? decodeURIComponent(opts.subject_name) : ''
  chapterName.value = ungroupedOnly.value ? '未分组' : (opts.chapter_name ? decodeURIComponent(opts.chapter_name) : '')
  uni.setNavigationBarTitle({ title: chapterName.value || '题目' })
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
.page { padding: 32rpx 32rpx 140rpx; background: var(--bg-page); min-height: 100vh; }
.header { padding: 20rpx 0 24rpx; }
.title { font-size: 36rpx; font-weight: 600; color: var(--text); display: block; }
.sub { font-size: 26rpx; color: var(--text-secondary); margin-top: 8rpx; display: block; }
.list { display: flex; flex-direction: column; gap: 16rpx; }
.item-wrap {
  position: relative;
  border-radius: 24rpx;
  overflow: hidden;
  background: var(--bg-card);
  box-shadow: var(--shadow-card);
}
.item-slide {
  position: relative;
  z-index: 1;
  width: 100%;
  padding: 28rpx 24rpx;
  background: var(--bg-card);
  transition: transform 0.2s ease;
  min-height: 100rpx;
  box-sizing: border-box;
}
.item-slide::after {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 120rpx;
  background: var(--bg-card);
  z-index: 0;
}
.item-main { position: relative; z-index: 1; min-width: 0; }
.content { font-size: 28rpx; color: var(--text); display: block; line-height: 1.4; }
.time { font-size: 24rpx; color: var(--text-hint); margin-top: 12rpx; display: block; }
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
.item-delete {
  right: 2rpx;
  width: 118rpx;
  border-radius: 0 14rpx 14rpx 0;
}
.empty { padding: 80rpx 32rpx; text-align: center; }
.empty-text { display: block; color: var(--text-secondary); font-size: 30rpx; }
.empty-hint { display: block; margin-top: 16rpx; color: var(--text-hint); font-size: 26rpx; }
.float-btn {
  position: fixed;
  right: 32rpx;
  bottom: 120rpx;
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
