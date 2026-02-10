<template>
  <view class="page">
    <view class="card actions">
      <button class="btn primary" @click="goImport">导入 PDF</button>
      <text class="hint">上传 PDF 并解析为错题，会占用存储空间</text>
    </view>

    <view class="card list-card">
      <text class="list-title">我的 PDF</text>
      <view v-if="loading" class="loading">加载中…</view>
      <view v-else-if="!list.length" class="empty">暂无 PDF，导入或从错题本导出后会显示在这里</view>
      <view v-else class="list">
        <view v-for="(item, i) in list" :key="item.filename" class="list-item">
          <view class="item-main">
            <text class="item-name">{{ item.display_name || item.filename || ('PDF ' + (i + 1)) }}</text>
            <text class="item-size">{{ formatSize(item.size) }}</text>
          </view>
          <view class="item-actions">
            <button class="btn-mini" @click="download(item)">下载</button>
            <button class="btn-mini danger" @click="confirmDelete(item)">删除</button>
          </view>
        </view>
      </view>
    </view>

    <view class="tabbar-placeholder" />
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listPdfs, deletePdf } from '@/api/import.js'
import { API_BASE_URL } from '@/config.js'

const list = ref([])
const loading = ref(true)

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function fullUrl(url) {
  if (!url) return ''
  const base = (API_BASE_URL || '').replace(/\/$/, '')
  return url.startsWith('http') ? url : base + (url.startsWith('/') ? url : '/' + url)
}

function loadList() {
  loading.value = true
  listPdfs()
    .then((data) => {
      list.value = Array.isArray(data) ? data : []
    })
    .catch((e) => {
      uni.showToast({ title: e.message || '加载失败', icon: 'none' })
      list.value = []
    })
    .finally(() => {
      loading.value = false
    })
}

function goImport() {
  uni.navigateTo({ url: '/pages/import/pdf' })
}

function getToken() {
  try {
    return uni.getStorageSync('token') || ''
  } catch (e) {
    return ''
  }
}

function download(item) {
  const url = fullUrl(item.url)
  if (!url) return
  const token = getToken()
  // #ifdef H5
  if (token) {
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => {
        if (!r.ok) throw new Error('下载失败')
        return r.blob()
      })
      .then((blob) => {
        const u = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = u
        a.download = item.display_name || item.filename || 'download.pdf'
        a.click()
        URL.revokeObjectURL(u)
        uni.showToast({ title: '已开始下载', icon: 'none' })
      })
      .catch(() => uni.showToast({ title: '下载失败', icon: 'none' }))
  } else {
    window.open(url, '_blank')
  }
  // #endif
  // #ifndef H5
  uni.downloadFile({
    url,
    header: token ? { Authorization: `Bearer ${token}` } : {},
    success: (res) => {
      if (res.statusCode !== 200) {
        uni.showToast({ title: '下载失败', icon: 'none' })
        return
      }
      // 先保存到本地再打开，避免临时文件被清理导致「文件已过期或已被清理」
      uni.saveFile({
        tempFilePath: res.tempFilePath,
        success: (saveRes) => {
          const savedPath = saveRes.savedFilePath
          if (savedPath) {
            uni.openDocument({
              filePath: savedPath,
              showMenu: true,
              fileType: 'pdf'
            })
            uni.showToast({ title: '已保存并打开', icon: 'none' })
          } else {
            uni.openDocument({
              filePath: res.tempFilePath,
              showMenu: true,
              fileType: 'pdf'
            })
          }
        },
        fail: () => {
          uni.openDocument({
            filePath: res.tempFilePath,
            showMenu: true,
            fileType: 'pdf'
          })
        }
      })
    },
    fail: () => uni.showToast({ title: '下载失败', icon: 'none' })
  })
  // #endif
}

function confirmDelete(item) {
  uni.showModal({
    title: '确认删除',
    content: '删除后无法恢复，且会释放存储空间。确定删除该 PDF？',
    success: (res) => {
      if (res.confirm) doDelete(item)
    }
  })
}

function doDelete(item) {
  uni.showLoading({ title: '删除中…' })
  deletePdf(item.filename)
    .then(() => {
      uni.hideLoading()
      uni.showToast({ title: '已删除', icon: 'success' })
      loadList()
    })
    .catch((e) => {
      uni.hideLoading()
      uni.showToast({ title: e.message || '删除失败', icon: 'none' })
    })
}

onMounted(loadList)
</script>

<style scoped>
.page { padding: 32rpx 32rpx 140rpx; background: var(--bg-page); min-height: 100vh; }
.card { background: var(--bg-card); border-radius: 24rpx; padding: 28rpx; margin-bottom: 32rpx; box-shadow: var(--shadow-card); }
.actions { }
.btn { width: 100%; height: 88rpx; line-height: 88rpx; border-radius: 44rpx; font-size: 30rpx; border: none; }
.btn.primary { background: var(--primary); color: #fff; }
.hint { display: block; font-size: 24rpx; color: var(--text-hint); margin-top: 16rpx; text-align: center; }
.list-title { font-size: 30rpx; font-weight: 600; color: var(--text); display: block; margin-bottom: 24rpx; }
.loading, .empty { font-size: 28rpx; color: var(--text-hint); text-align: center; padding: 48rpx; }
.list { }
.list-item { display: flex; align-items: center; justify-content: space-between; padding: 24rpx 0; border-bottom: 1rpx solid #f0f0f0; }
.list-item:last-child { border-bottom: none; }
.item-main { flex: 1; min-width: 0; }
.item-name { font-size: 28rpx; color: var(--text); display: block; }
.item-size { font-size: 24rpx; color: var(--text-hint); }
.item-actions { display: flex; gap: 16rpx; flex-shrink: 0; }
.btn-mini { padding: 12rpx 24rpx; font-size: 24rpx; border-radius: 8rpx; background: var(--primary-bg); color: var(--primary); border: none; }
.btn-mini.danger { background: #ffebee; color: #c62828; }
.btn-mini::after { border: none; }
.tabbar-placeholder { height: 120rpx; }
</style>
