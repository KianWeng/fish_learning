<template>
  <view class="page">
    <view class="list" v-if="list.length">
      <view class="item" v-for="s in list" :key="s.id">
        <text class="name">{{ s.name }}</text>
        <view class="actions">
          <text class="link" @click="goChapters(s)">章节</text>
          <text class="link" @click="goEdit(s)">编辑</text>
          <text class="link danger" @click="onDelete(s)">删除</text>
        </view>
      </view>
    </view>
    <view class="empty" v-else-if="!loading">暂无科目，点击右下角 + 添加</view>
    <view class="empty" v-else>加载中...</view>

    <view class="float-btn" @click="onAddTap">+</view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { listSubjects, deleteSubject } from '@/api/subjects.js'
import { setSourcePath, getResultPath } from '@/utils/crop-store.js'

const list = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    list.value = await listSubjects()
  } catch (e) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

/** 添加：新建错题本(科目) 或 拍照添加题目 */
function onAddTap() {
  uni.showActionSheet({
    itemList: ['新建错题本', '拍照添加题目'],
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
  uni.navigateTo({ url: '/pages/subjects/edit' })
}

function goEdit(s) {
  uni.navigateTo({ url: `/pages/subjects/edit?id=${s.id}&name=${encodeURIComponent(s.name)}&sort=${s.sort}` })
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
.item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 28rpx;
  background: var(--bg-card);
  border-radius: 24rpx;
  box-shadow: var(--shadow-card);
}
.name { font-size: 30rpx; font-weight: 500; color: var(--text); }
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
