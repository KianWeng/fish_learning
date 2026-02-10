<template>
  <view class="page">
    <view v-if="loading" class="loading-wrap">
      <text class="loading-text">正在生成报告…</text>
    </view>
    <template v-else>
      <view class="header-row">
        <text class="subject-name">{{ subjectName }}</text>
        <button class="btn-export" :disabled="exporting" @click="onExportPdf">导出报告 PDF</button>
      </view>

      <view class="card report-card">
        <text class="card-title">报告正文</text>
        <text class="report-text">{{ report }}</text>
      </view>

      <view class="card map-card">
        <text class="card-title">知识点总结</text>
        <view class="tree-wrap" v-if="hasTree">
          <view class="tree-node root">
            <text class="node-label">{{ knowledgeMap.label || subjectName }}</text>
            <text class="node-meta" v-if="nodeMeta(knowledgeMap)">{{ nodeMeta(knowledgeMap) }}</text>
          </view>
          <KnowledgeTree v-if="knowledgeMap.children?.length" :nodes="knowledgeMap.children" :depth="1" />
        </view>
        <text v-else class="empty-tree">暂无知识点结构</text>
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { API_BASE_URL } from '@/config.js'
import { getSubjectReport, exportReportPdf } from '@/api/subjects.js'
import KnowledgeTree from './KnowledgeTree.vue'

const subjectId = ref(0)
const subjectName = ref('')
const report = ref('')
const knowledgeMap = ref({ label: '', children: [] })
const loading = ref(true)
const exporting = ref(false)

const hasTree = computed(() => {
  const m = knowledgeMap.value
  return (m && m.label) || (m.children && m.children.length > 0)
})

function nodeMeta(node) {
  if (!node) return ''
  const count = node.count
  const mastered = node.mastered
  if (count != null && mastered != null) return `${mastered}/${count} 已掌握`
  if (count != null) return `${count} 题`
  return ''
}

onLoad((options) => {
  const id = options?.subject_id ? Number(options.subject_id) : 0
  subjectId.value = id
  if (options?.subject_name) subjectName.value = decodeURIComponent(options.subject_name)
  uni.setNavigationBarTitle({ title: subjectName.value || '生成学习报告' })
})

onMounted(async () => {
  if (!subjectId.value) {
    loading.value = false
    report.value = '请从错题本列表进入生成学习报告。'
    return
  }
  try {
    const res = await getSubjectReport(subjectId.value)
    subjectName.value = res.subject_name || subjectName.value
    report.value = res.report || ''
    knowledgeMap.value = res.knowledge_map && typeof res.knowledge_map === 'object'
      ? res.knowledge_map
      : { label: subjectName.value, children: [] }
    if (subjectName.value) uni.setNavigationBarTitle({ title: subjectName.value + ' - 生成学习报告' })
  } catch (e) {
    report.value = e.message || '加载报告失败'
    knowledgeMap.value = { label: subjectName.value || '错题本', children: [] }
  } finally {
    loading.value = false
  }
})

async function onExportPdf() {
  if (!subjectId.value) {
    uni.showToast({ title: '无法导出', icon: 'none' })
    return
  }
  exporting.value = true
  try {
    const res = await exportReportPdf(subjectId.value)
    const url = (res.url || '').startsWith('http')
      ? res.url
      : (API_BASE_URL.replace(/\/$/, '') + (res.url.startsWith('/') ? res.url : '/' + res.url))
    const token = uni.getStorageSync('token') || ''
    uni.downloadFile({
      url,
      header: token ? { Authorization: 'Bearer ' + token } : {},
      success: (d) => {
        if (d.statusCode === 200) {
          uni.openDocument({ filePath: d.tempFilePath, showMenu: true, fileType: 'pdf' })
          uni.showToast({ title: '已打开 PDF' })
        } else {
          uni.showToast({ title: '下载失败', icon: 'none' })
        }
      },
      fail: () => uni.showToast({ title: '下载失败', icon: 'none' })
    })
  } catch (e) {
    const msg = e.message || '导出失败'
    if (msg.includes('积分不足')) {
      uni.showModal({
        title: '积分不足',
        content: msg + '。可在「我的」页观看激励视频获取积分。',
        cancelText: '观看广告',
        confirmText: '确定',
        success: (res) => {
          if (res.cancel) uni.navigateTo({ url: '/pages/my/index' })
        }
      })
    } else {
      uni.showToast({ title: msg, icon: 'none' })
    }
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped>
.page { padding: 24rpx 32rpx 60rpx; background: var(--bg-page); min-height: 100vh; }
.loading-wrap { padding: 80rpx; text-align: center; }
.loading-text { font-size: 28rpx; color: var(--text-hint); }
.header-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24rpx; flex-wrap: wrap; gap: 16rpx; }
.subject-name { font-size: 34rpx; font-weight: 600; color: var(--text); flex: 1; }
.btn-export { padding: 16rpx 28rpx; font-size: 26rpx; background: var(--primary); color: #fff; border: none; border-radius: 16rpx; }
.btn-export::after { border: none; }
.card { background: var(--bg-card); border-radius: 24rpx; padding: 28rpx; margin-bottom: 24rpx; box-shadow: var(--shadow-card); }
.card-title { display: block; font-size: 28rpx; font-weight: 600; color: var(--text); margin-bottom: 16rpx; }
.report-text { font-size: 28rpx; color: var(--text); line-height: 1.6; white-space: pre-wrap; word-break: break-all; }
.tree-wrap { margin-top: 8rpx; }
.tree-node { margin-bottom: 12rpx; }
.tree-node.root { margin-bottom: 16rpx; }
.node-label { font-size: 28rpx; color: var(--text); font-weight: 500; }
.node-meta { font-size: 24rpx; color: var(--text-hint); margin-left: 12rpx; }
.empty-tree { font-size: 26rpx; color: var(--text-hint); }
</style>
