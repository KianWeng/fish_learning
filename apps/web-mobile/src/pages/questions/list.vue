<template>
  <view class="page">
    <view class="header">
      <text class="title">我的错题本</text>
      <text class="sub" v-if="list.length">{{ list.length }} 个</text>
      <view class="header-right">
        <text class="link" @click="onAddTap">添加</text>
        <text class="link" @click="goStats">数据统计</text>
        <text class="link" @click="goAllQuestions">全部错题</text>
      </view>
    </view>

    <view class="list-wrap" v-if="list.length">
      <view class="book-grid">
        <view
          class="book-card"
          v-for="s in list"
          :key="s.id"
          @click="goChapters(s)"
        >
          <view class="card-cover" :class="coverUrl(s) ? 'has-img' : ''">
            <image v-if="coverUrl(s)" :src="coverUrl(s)" mode="aspectFill" class="cover-img" />
            <view v-else class="cover-placeholder"></view>
            <view class="card-menu-btn" @click.stop="openCardMenu(s)">
              <view class="menu-dot"></view>
              <view class="menu-dot"></view>
              <view class="menu-dot"></view>
            </view>
          </view>
          <view class="card-footer">
            <text class="book-name">{{ s.name }}</text>
            <view class="progress-wrap">
              <view class="progress-bar"><view class="progress-inner" :style="{ width: getBarWidth(s) + '%' }"></view></view>
              <text class="progress-text">{{ getCount(s) }} 题</text>
            </view>
          </view>
        </view>
      </view>
    </view>
    <view class="empty" v-else-if="!loading">
      <text class="empty-text">暂无错题本</text>
      <text class="empty-hint">点击右下角 + 可选择「新建错题本」或「拍照添加题目」</text>
    </view>

    <view class="float-btn" @click="onAddTap">+</view>

    <view class="tabbar-placeholder" />
    <TabBar current="questions" />
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import TabBar from '@/components/TabBar.vue'
import { API_BASE_URL } from '@/config.js'
import { listSubjects, updateSubject, deleteSubject, exportSubjectPdf } from '@/api/subjects.js'
import { listQuestions } from '@/api/questions.js'
import { uploadImage } from '@/api/questions.js'
import { setSourcePath, getResultPath } from '@/utils/crop-store.js'

const list = ref([])
const loading = ref(true)
const subjectCounts = ref({})

function coverUrl(s) {
  if (!s?.cover_url) return ''
  const url = s.cover_url
  return url.startsWith('http') ? url : API_BASE_URL + url
}

async function load() {
  loading.value = true
  try {
    list.value = await listSubjects()
    for (const s of list.value) {
      const res = await listQuestions({ subject_id: s.id })
      subjectCounts.value[s.id] = res.length
    }
  } catch (e) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

/** 该错题本题目数量 */
function getCount(s) {
  return subjectCounts.value[s.id] || 0
}

/** 进度条宽度百分比：按题目数量，约 30 题为满格 */
function getBarWidth(s) {
  const n = getCount(s)
  return n <= 0 ? 0 : Math.min(100, (n / 30) * 100)
}

function goChapters(s) {
  uni.navigateTo({ url: `/pages/chapters/list?subject_id=${s.id}&subject_name=${encodeURIComponent(s.name)}` })
}

function openCardMenu(s) {
  uni.showActionSheet({
    itemList: ['导出 PDF', '重命名', '替换封面', '删除'],
    success: (res) => {
      if (res.tapIndex === 0) exportPdf(s)
      else if (res.tapIndex === 1) goRename(s)
      else if (res.tapIndex === 2) changeCover(s)
      else if (res.tapIndex === 3) doDelete(s)
    }
  })
}

async function exportPdf(s) {
  uni.showLoading({ title: '生成中...' })
  try {
    const res = await exportSubjectPdf(s.id)
    const url = (res.url || '').startsWith('http') ? res.url : (API_BASE_URL.replace(/\/$/, '') + (res.url.startsWith('/') ? res.url : '/' + res.url))
    const token = uni.getStorageSync('token') || ''
    uni.hideLoading()
    uni.downloadFile({
      url,
      header: token ? { Authorization: 'Bearer ' + token } : {},
      success: (d) => {
        if (d.statusCode === 200) {
          uni.openDocument({
            filePath: d.tempFilePath,
            showMenu: true,
            fileType: 'pdf'
          })
        } else {
          uni.showToast({ title: '下载失败', icon: 'none' })
        }
      },
      fail: () => uni.showToast({ title: '下载失败', icon: 'none' })
    })
  } catch (e) {
    uni.hideLoading()
    uni.showToast({ title: e.message || '导出失败', icon: 'none' })
  }
}

function goRename(s) {
  uni.navigateTo({
    url: `/pages/subjects/edit?id=${s.id}&name=${encodeURIComponent(s.name)}&sort=${s.sort || 0}`
  })
}

async function changeCover(s) {
  uni.chooseImage({
    count: 1,
    sourceType: ['album', 'camera'],
    success: async (res) => {
      const path = res.tempFilePaths[0]
      uni.showLoading({ title: '上传中...' })
      try {
        const data = await uploadImage(path)
        const url = data.url || ''
        await updateSubject(s.id, { cover_url: url })
        s.cover_url = url
        uni.hideLoading()
        uni.showToast({ title: '封面已更换' })
      } catch (e) {
        uni.hideLoading()
        uni.showToast({ title: e.message || '更换失败', icon: 'none' })
      }
    }
  })
}

async function doDelete(s) {
  const ok = await new Promise(r => {
    uni.showModal({
      title: '确认删除',
      content: `删除错题本「${s.name}」？其下章节与错题将一并删除。`,
      success: res => r(res.confirm)
    })
  })
  if (!ok) return
  try {
    await deleteSubject(s.id)
    list.value = list.value.filter(x => x.id !== s.id)
    uni.showToast({ title: '已删除' })
  } catch (e) {
    uni.showToast({ title: e.message || '删除失败', icon: 'none' })
  }
}

function goCreateWithPhoto() {
  uni.navigateTo({ url: '/pages/subjects/create-with-photo' })
}

/** 直接调起相机，拍完进入裁剪，裁剪后返回本页再由 onShow 跳添加页 */
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

/** 点击添加：可选新建错题本或拍照添加题目 */
function onAddTap() {
  uni.showActionSheet({
    itemList: ['新建错题本', '拍照添加题目'],
    success: (res) => {
      if (res.tapIndex === 0) goCreateWithPhoto()
      else if (res.tapIndex === 1) openCameraThenCrop()
    }
  })
}

function goAddWithCamera() {
  openCameraThenCrop()
}

onLoad(() => {
  uni.setNavigationBarTitle({ title: '我的错题本' })
})

onShow(() => {
  if (getResultPath()) {
    uni.navigateTo({ url: '/pages/questions/add' })
  }
})

function goAllQuestions() {
  uni.navigateTo({ url: '/pages/questions/all' })
}

function goStats() {
  uni.navigateTo({ url: '/pages/stats/index' })
}

onMounted(() => {
  load()
  const pages = getCurrentPages()
  const page = pages[pages.length - 1]
  const opts = page.options || {}
  if (opts.openCamera === '1') {
    setTimeout(openCameraThenCrop, 100)
  }
})
</script>

<style scoped>
.page {
  padding: 24rpx 24rpx 140rpx;
  background: linear-gradient(180deg, #f0f4fa 0%, #e8eef5 100%);
  min-height: 100vh;
}
.header {
  position: relative;
  padding: 20rpx 0 28rpx;
}
.title { font-size: 40rpx; font-weight: 600; color: #1a1a2e; }
.sub { display: block; font-size: 26rpx; color: #6b7280; margin-top: 6rpx; }
.header-right {
  position: absolute;
  right: 0;
  top: 20rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
}
.link { font-size: 26rpx; color: #1989fa; }

.list-wrap {
  max-width: 680rpx;
  margin: 0 auto;
}
.book-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24rpx;
}
.book-card {
  background: #fff;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.06);
}
.card-cover {
  height: 180rpx;
  position: relative;
  overflow: hidden;
}
.cover-img {
  width: 100%;
  height: 100%;
  display: block;
}
.cover-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(145deg, #a8d8ea 0%, #7eb8da 50%, #5a9fc9 100%);
}
.card-menu-btn {
  position: absolute;
  top: 8rpx;
  right: 8rpx;
  width: 40rpx;
  height: 40rpx;
  background: rgba(0,0,0,0.4);
  border-radius: 6rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
}
.menu-dot {
  width: 5rpx;
  height: 5rpx;
  border-radius: 50%;
  background: #fff;
}
.card-footer { padding: 20rpx; }
.book-name {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.progress-wrap {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 12rpx;
}
.progress-bar {
  flex: 1;
  height: 8rpx;
  background: #eee;
  border-radius: 4rpx;
  overflow: hidden;
}
.progress-inner {
  height: 100%;
  background: linear-gradient(90deg, #1989fa, #0d6ef5);
  border-radius: 4rpx;
  transition: width 0.3s;
}
.progress-text { font-size: 22rpx; color: #999; }

.empty {
  text-align: center;
  padding: 80rpx 32rpx;
}
.empty-text { display: block; color: #6b7280; font-size: 30rpx; }
.empty-hint { display: block; margin-top: 16rpx; color: #9ca3af; font-size: 26rpx; }

.float-btn {
  position: fixed;
  right: 32rpx;
  bottom: 220rpx;
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
.tabbar-placeholder { height: 120rpx; }
</style>
