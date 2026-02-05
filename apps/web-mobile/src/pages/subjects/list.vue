<template>
  <view class="page">
    <view class="toolbar">
      <button class="btn primary" @click="goAdd">添加科目</button>
    </view>
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
    <view class="empty" v-else-if="!loading">暂无科目，请添加</view>
    <view class="empty" v-else>加载中...</view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listSubjects, deleteSubject } from '@/api/subjects.js'

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

onMounted(load)
</script>

<style scoped>
.page { padding: 24rpx; }
.toolbar { margin-bottom: 24rpx; }
.btn { padding: 24rpx; border-radius: 12rpx; font-size: 30rpx; }
.primary { background: #07c160; color: #fff; border: none; }
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
</style>
