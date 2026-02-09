<template>
  <view class="page">
    <view class="list" v-if="list.length">
      <view class="item" v-for="c in list" :key="c.id" @click="goChapterQuestions(c)">
        <text class="name">{{ c.name }}</text>
        <view class="actions" @click.stop>
          <text class="link" @click="goEdit(c)">编辑</text>
          <text class="link danger" @click="onDelete(c)">删除</text>
        </view>
      </view>
    </view>
    <view class="empty" v-else-if="!loading">暂无章节，点击右下角 + 添加</view>
    <view class="empty" v-else>加载中...</view>

    <view class="float-btn" @click="onAddTap">+</view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { listChapters, deleteChapter } from '@/api/chapters.js'
import { setSourcePath, getResultPath } from '@/utils/crop-store.js'

const subjectId = ref(0)
const subjectName = ref('')
const list = ref([])
const loading = ref(true)

async function load() {
  if (!subjectId.value) return
  loading.value = true
  try {
    list.value = await listChapters(subjectId.value)
  } catch (e) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

/** 点击添加：新建章节目录 或 拍照添加题目 */
function onAddTap() {
  uni.showActionSheet({
    itemList: ['新建章节目录', '拍照添加题目'],
    success: (res) => {
      if (res.tapIndex === 0) goAdd()
      else if (res.tapIndex === 1) openCameraThenCrop()
    }
  })
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
  uni.navigateTo({ url: `/pages/chapters/edit?subject_id=${subjectId.value}&subject_name=${encodeURIComponent(subjectName.value)}` })
}

function goEdit(c) {
  uni.navigateTo({ url: `/pages/chapters/edit?id=${c.id}&subject_id=${subjectId.value}&name=${encodeURIComponent(c.name)}&sort=${c.sort}` })
}

function goChapterQuestions(c) {
  uni.navigateTo({
    url: `/pages/chapters/questions?subject_id=${subjectId.value}&chapter_id=${c.id}&subject_name=${encodeURIComponent(subjectName.value)}&chapter_name=${encodeURIComponent(c.name)}`
  })
}

async function onDelete(c) {
  const ok = await new Promise(r => uni.showModal({ title: '确认删除', content: `删除章节「${c.name}」？`, success: res => r(res.confirm) }))
  if (!ok) return
  try {
    await deleteChapter(c.id)
    uni.showToast({ title: '已删除' })
    load()
  } catch (e) {
    uni.showToast({ title: e.message || '删除失败', icon: 'none' })
  }
}

function initFromOptions(opts) {
  if (!opts) {
    const pages = getCurrentPages()
    const page = pages[pages.length - 1]
    opts = page.options || {}
  }
  subjectId.value = parseInt(opts.subject_id, 10) || 0
  subjectName.value = opts.subject_name ? decodeURIComponent(opts.subject_name) : ''
  uni.setNavigationBarTitle({ title: subjectName.value || '' })
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
    uni.navigateTo({
      url: `/pages/questions/add?subject_id=${subjectId.value}&subject_name=${encodeURIComponent(subjectName.value)}`
    })
  }
})
</script>

<style scoped>
.page { padding: 24rpx 24rpx 140rpx; min-height: 100vh; background: #f5f6fa; }
.list { display: flex; flex-direction: column; gap: 16rpx; }
.item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 28rpx; background: #fff; border-radius: 12rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}
.name { font-size: 30rpx; font-weight: 500; }
.actions { display: flex; gap: 24rpx; }
.link { font-size: 26rpx; color: #07c160; }
.link.danger { color: #ee0a24; }
.empty { padding: 60rpx; text-align: center; color: #999; font-size: 28rpx; }
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
