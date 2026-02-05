<template>
  <view class="page">
    <view class="header">
      <text class="title">我的错题本</text>
      <text class="sub" v-if="list.length">{{ list.length }} 个科目</text>
      <view class="header-right">
        <text class="link" @click="goStats">数据统计</text>
        <view class="search" @click="goSearch">🔍</view>
      </view>
    </view>

    <view class="list" v-if="list.length">
      <view class="book-card" v-for="s in list" :key="s.id" @click="goChapters(s)">
        <view class="card-cover"></view>
        <view class="card-footer">
          <text class="book-name">{{ s.name }}</text>
          <view class="progress-wrap">
            <view class="progress-bar"><view class="progress-inner" :style="{ width: getProgress(s) + '%' }"></view></view>
            <text class="progress-text">{{ getProgress(s) }}%</text>
          </view>
        </view>
      </view>
    </view>
    <view class="empty" v-else-if="!loading">
      <text>暂无错题本</text>
      <view class="btn-add" @click="showSheet = true">新建错题本</view>
    </view>

    <view class="float-btn" @click="showSheet = true">+</view>

    <!-- 底部弹窗：创建或扫描 -->
    <view class="mask" v-if="showSheet" @click="showSheet = false"></view>
    <view class="sheet" :class="{ show: showSheet }">
      <view class="sheet-title">创建或扫描</view>
      <view class="sheet-actions">
        <view class="sheet-btn blue" @click="goAddSubject">
          <text class="sheet-icon">📁</text>
          <text class="sheet-text">新建错题本</text>
        </view>
        <view class="sheet-btn orange" @click="goPhoto">
          <text class="sheet-icon">📷</text>
          <text class="sheet-text">拍照</text>
        </view>
      </view>
    </view>

    <view class="tabbar-placeholder" />
    <TabBar current="my" />
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import TabBar from '@/components/TabBar.vue'
import { listSubjects } from '@/api/subjects.js'
import { listQuestions } from '@/api/questions.js'

const list = ref([])
const loading = ref(true)
const showSheet = ref(false)
const subjectCounts = ref({})

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

function getProgress(s) {
  const total = subjectCounts.value[s.id] || 0
  return total > 0 ? Math.min(100, 50) : 0
}

function goChapters(s) {
  uni.navigateTo({ url: `/pages/chapters/list?subject_id=${s.id}&subject_name=${encodeURIComponent(s.name)}` })
}

function goAddSubject() {
  showSheet.value = false
  uni.navigateTo({ url: '/pages/subjects/edit' })
}

function goPhoto() {
  showSheet.value = false
  uni.navigateTo({ url: '/pages/questions/add' })
}

function goSearch() {
  uni.navigateTo({ url: '/pages/questions/list' })
}

function goStats() {
  uni.navigateTo({ url: '/pages/stats/index' })
}

onMounted(load)
</script>

<style scoped>
.page { padding: 24rpx 24rpx 140rpx; background: #f0f1f5; min-height: 100vh; }
.header { position: relative; padding: 24rpx 0; }
.title { font-size: 40rpx; font-weight: 600; color: #333; }
.sub { display: block; font-size: 26rpx; color: #999; margin-top: 8rpx; }
.header-right { position: absolute; right: 0; top: 24rpx; display: flex; align-items: center; gap: 24rpx; }
.link { font-size: 26rpx; color: #1989fa; }
.search { font-size: 40rpx; }
.list { display: flex; flex-direction: column; gap: 24rpx; }
.book-card { background: #fff; border-radius: 24rpx; overflow: hidden; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.06); }
.card-cover { height: 160rpx; background: linear-gradient(135deg, #a8d8ea 0%, #7eb8da 100%); }
.card-footer { padding: 24rpx; }
.book-name { font-size: 32rpx; font-weight: 500; color: #333; }
.progress-wrap { display: flex; align-items: center; gap: 16rpx; margin-top: 16rpx; }
.progress-bar { flex: 1; height: 12rpx; background: #eee; border-radius: 6rpx; overflow: hidden; }
.progress-inner { height: 100%; background: #1989fa; border-radius: 6rpx; transition: width 0.3s; }
.progress-text { font-size: 24rpx; color: #999; }
.empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.btn-add { margin-top: 24rpx; color: #1989fa; font-size: 28rpx; }
.float-btn { position: fixed; right: 32rpx; bottom: 160rpx; width: 96rpx; height: 96rpx; background: #1989fa; color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 48rpx; box-shadow: 0 8rpx 24rpx rgba(25,137,250,0.4); z-index: 10; }
.mask { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 98; }
.sheet { position: fixed; left: 0; right: 0; bottom: 0; background: #fff; border-radius: 32rpx 32rpx 0 0; padding: 32rpx 32rpx calc(32rpx + env(safe-area-inset-bottom)); z-index: 99; transform: translateY(100%); transition: transform 0.3s; }
.sheet.show { transform: translateY(0); }
.sheet-title { font-size: 34rpx; font-weight: 600; color: #333; margin-bottom: 32rpx; text-align: center; }
.sheet-actions { display: flex; gap: 24rpx; }
.sheet-btn { flex: 1; padding: 40rpx; border-radius: 20rpx; text-align: center; }
.sheet-btn.blue { background: #e8f4ff; }
.sheet-btn.orange { background: #fff4e6; }
.sheet-icon { display: block; font-size: 56rpx; margin-bottom: 12rpx; }
.sheet-text { font-size: 28rpx; color: #333; }
.tabbar-placeholder { height: 120rpx; }
</style>
