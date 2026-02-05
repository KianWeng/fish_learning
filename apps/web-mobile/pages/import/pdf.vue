<template>
  <view class="page">
    <view class="form card">
      <view class="field">
        <text class="label">导入到科目</text>
        <picker :range="subjects" range-key="name" @change="onSubjectChange">
          <view class="picker">{{ subjectName || '请选择科目' }}</view>
        </picker>
      </view>
      <view class="field" v-if="subjectId">
        <text class="label">章节（可选）</text>
        <picker :range="chapterOptions" range-key="name" @change="onChapterChange">
          <view class="picker">{{ chapterName || '不指定章节' }}</view>
        </picker>
      </view>
      <view class="field">
        <text class="label">PDF 文件</text>
        <!-- #ifdef H5 -->
        <input type="file" accept=".pdf" class="file-input" @change="onFileSelect" />
        <view class="file-tip" v-if="!file">请选择错题集 PDF</view>
        <view class="file-tip" v-else>已选: {{ file.name }}</view>
        <!-- #endif -->
        <!-- #ifndef H5 -->
        <button class="btn default" @click="choosePdf">选择 PDF 文件</button>
        <view class="file-tip" v-if="filePath">{{ filePath }}</view>
        <!-- #endif -->
      </view>
      <button class="btn primary" :disabled="!canImport || importing" @click="doImport">
        {{ importing ? '导入中…' : '开始导入' }}
      </button>
    </view>
    <view class="result card" v-if="result">
      <text>导入完成：共 {{ result.created }} 道题</text>
    </view>
  </view>
</template>

<script setup>
import { ref, watch } from 'vue'
import { listSubjects } from '@/api/subjects.js'
import { listChapters } from '@/api/chapters.js'
import { importPdf } from '@/api/import.js'

const subjectId = ref(0)
const subjectName = ref('')
const chapterId = ref(null)
const chapterName = ref('')
const subjects = ref([])
const chapters = ref([])
const chapterOptions = ref([{ id: null, name: '不指定章节' }])
const file = ref(null)
const filePath = ref('')
const importing = ref(false)
const result = ref(null)

const canImport = ref(false)
watch([subjectId, file, filePath], () => {
  canImport.value = subjectId.value && (file.value || filePath.value)
})

async function loadSubjects() {
  try {
    subjects.value = await listSubjects()
  } catch (e) {
    uni.showToast({ title: e.message || '加载失败', icon: 'none' })
  }
}

watch(subjectId, async (id) => {
  if (!id) {
    chapters.value = []
    chapterOptions.value = [{ id: null, name: '不指定章节' }]
    return
  }
  try {
    chapters.value = await listChapters(id)
    const s = subjects.value.find((x) => x.id === id)
    subjectName.value = s ? s.name : ''
    chapterOptions.value = [{ id: null, name: '不指定章节' }, ...chapters.value]
  } catch (e) {
    chapters.value = []
    chapterOptions.value = [{ id: null, name: '不指定章节' }]
  }
  chapterId.value = null
  chapterName.value = ''
})

function onSubjectChange(e) {
  const i = e.detail.value
  if (subjects.value[i]) {
    subjectId.value = subjects.value[i].id
    subjectName.value = subjects.value[i].name
  }
}

function onChapterChange(e) {
  const i = e.detail.value
  const opts = chapterOptions.value[i]
  if (opts) {
    chapterId.value = opts.id
    chapterName.value = opts.name
  }
}

function onFileSelect(e) {
  const t = e.target
  if (t && t.files && t.files[0]) file.value = t.files[0]
}

function choosePdf() {
  // #ifdef MP-WEIXIN
  uni.chooseMessageFile({
    count: 1,
    type: 'file',
    extension: ['pdf'],
    success: (res) => {
      filePath.value = res.tempFiles[0].path
    },
  })
  // #endif
  // #ifdef APP-PLUS
  // 可扩展为 plus.gallery.pick 等
  uni.showToast({ title: '请使用 H5 或微信小程序导入', icon: 'none' })
  // #endif
}

async function doImport() {
  if (!subjectId.value) {
    uni.showToast({ title: '请选择科目', icon: 'none' })
    return
  }
  if (file.value || filePath.value) {
    importing.value = true
    result.value = null
    try {
      const data = file.value
        ? await importPdf({ file: file.value, subjectId: subjectId.value, chapterId: chapterId.value })
        : await importPdf({ filePath: filePath.value, subjectId: subjectId.value, chapterId: chapterId.value })
      result.value = data
      uni.showToast({ title: `已导入 ${data.created} 道题` })
    } catch (e) {
      uni.showToast({ title: e.message || '导入失败', icon: 'none' })
    } finally {
      importing.value = false
    }
  }
}

loadSubjects()
</script>

<style scoped>
.page { padding: 24rpx; }
.card { background: #fff; border-radius: 12rpx; padding: 32rpx; margin-bottom: 24rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06); }
.field { margin-bottom: 24rpx; }
.label { display: block; font-size: 28rpx; color: #666; margin-bottom: 8rpx; }
.picker { padding: 24rpx; border: 1rpx solid #eee; border-radius: 8rpx; font-size: 30rpx; }
.file-input { font-size: 28rpx; }
.file-tip { font-size: 24rpx; color: #999; margin-top: 8rpx; }
.btn { margin-top: 16rpx; padding: 28rpx; border-radius: 12rpx; font-size: 30rpx; width: 100%; }
.primary { background: #07c160; color: #fff; border: none; }
.default { background: #f0f0f0; color: #333; border: none; }
.result { font-size: 28rpx; }
</style>
