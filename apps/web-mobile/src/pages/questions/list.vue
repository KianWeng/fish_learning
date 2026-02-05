<template>
  <view class="page">
    <view class="filter">
      <picker :range="subjectOptions" range-key="name" @change="onSubjectChange">
        <view class="filter-item">{{ subjectName || '全部科目' }}</view>
      </picker>
      <picker v-if="subjectId" :range="chapterOptions" range-key="name" @change="onChapterChange">
        <view class="filter-item">{{ chapterName || '全部章节' }}</view>
      </picker>
    </view>
    <view class="list" v-if="list.length">
      <view class="item" v-for="q in list" :key="q.id" @click="goDetail(q.id)">
        <text class="content">{{ q.content }}</text>
        <text class="time">{{ q.created_at }}</text>
      </view>
    </view>
    <view class="empty" v-else-if="!loading">暂无错题</view>
    <view class="empty" v-else>加载中...</view>
    <view class="tabbar-placeholder" />
    <TabBar current="questions" />
  </view>
</template>

<script setup>
import { ref, watch } from 'vue'
import TabBar from '@/components/TabBar.vue'
import { listSubjects } from '@/api/subjects.js'
import { listChapters } from '@/api/chapters.js'
import { listQuestions } from '@/api/questions.js'

const list = ref([])
const loading = ref(true)
const subjectId = ref(null)
const subjectName = ref('')
const chapterId = ref(null)
const chapterName = ref('')
const subjects = ref([])
const chapters = ref([])
const subjectOptions = ref([{ id: null, name: '全部科目' }])
const chapterOptions = ref([{ id: null, name: '全部章节' }])

async function load() {
  loading.value = true
  try {
    const params = {}
    if (subjectId.value) params.subject_id = subjectId.value
    if (chapterId.value) params.chapter_id = chapterId.value
    list.value = await listQuestions(params)
  } catch (e) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function loadSubjects() {
  try {
    subjects.value = await listSubjects()
    subjectOptions.value = [{ id: null, name: '全部科目' }, ...subjects.value]
  } catch (e) {
    subjects.value = []
    subjectOptions.value = [{ id: null, name: '全部科目' }]
  }
}

watch(subjectId, async (id) => {
  if (!id) { chapters.value = []; chapterOptions.value = [{ id: null, name: '全部章节' }]; chapterId.value = null; chapterName.value = ''; load(); return }
  try {
    chapters.value = await listChapters(id)
    chapterOptions.value = [{ id: null, name: '全部章节' }, ...chapters.value]
    const s = subjects.value.find(x => x.id === id)
    subjectName.value = s ? s.name : ''
  } catch (e) {
    chapters.value = []
    chapterOptions.value = [{ id: null, name: '全部章节' }]
  }
  chapterId.value = null
  chapterName.value = ''
  load()
})

watch(chapterId, () => load())

function onSubjectChange(e) {
  const i = parseInt(e.detail.value, 10)
  const opts = subjectOptions.value[i]
  if (opts && opts.id == null) {
    subjectId.value = null
    subjectName.value = ''
  } else if (opts) {
    subjectId.value = opts.id
    subjectName.value = opts.name
  }
}

function onChapterChange(e) {
  const i = parseInt(e.detail.value, 10)
  const opts = chapterOptions.value[i]
  if (opts && opts.id == null) {
    chapterId.value = null
    chapterName.value = ''
  } else if (opts) {
    chapterId.value = opts.id
    chapterName.value = opts.name
  }
}

function goDetail(id) {
  uni.navigateTo({ url: `/pages/questions/detail?id=${id}` })
}

loadSubjects().then(() => load())
</script>

<style scoped>
.page { padding: 24rpx 24rpx 140rpx; background: #f5f6fa; min-height: 100vh; }
.filter { display: flex; gap: 16rpx; margin-bottom: 24rpx; flex-wrap: wrap; }
.filter-item { padding: 16rpx 24rpx; background: #fff; border-radius: 8rpx; font-size: 26rpx; box-shadow: 0 2rpx 6rpx rgba(0,0,0,0.06); }
.list { display: flex; flex-direction: column; gap: 16rpx; }
.item { padding: 28rpx; background: #fff; border-radius: 12rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06); }
.content { font-size: 28rpx; color: #333; display: block; }
.time { font-size: 24rpx; color: #999; margin-top: 12rpx; display: block; }
.empty { padding: 60rpx; text-align: center; color: #999; font-size: 28rpx; }
.tabbar-placeholder { height: 120rpx; }
</style>
