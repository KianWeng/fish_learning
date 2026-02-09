<template>
  <view class="page">
    <view class="form">
      <view class="row">
        <text class="label">章节名称</text>
        <input class="input" v-model="form.name" placeholder="请输入章节名称" />
      </view>
      <view class="row">
        <text class="label">排序</text>
        <input class="input" type="number" v-model.number="form.sort" placeholder="0" />
      </view>
      <button class="btn primary" @click="submit">保存</button>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { createChapter, updateChapter } from '@/api/chapters.js'

const id = ref(null)
const subjectId = ref(0)
const form = ref({ name: '', sort: 0 })

function applyOptions(opts) {
  if (!opts) return
  subjectId.value = parseInt(opts.subject_id, 10) || 0
  if (opts.id) {
    id.value = parseInt(opts.id, 10)
    form.value.name = opts.name ? decodeURIComponent(opts.name) : ''
    form.value.sort = parseInt(opts.sort, 10) || 0
    uni.setNavigationBarTitle({ title: form.value.name || '' })
  } else {
    uni.setNavigationBarTitle({ title: '' })
  }
}

onLoad((opts) => {
  applyOptions(opts)
})

onMounted(() => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1]
  applyOptions(page.options || {})
})

async function submit() {
  if (!form.value.name.trim()) {
    uni.showToast({ title: '请输入章节名称', icon: 'none' })
    return
  }
  try {
    if (id.value) {
      await updateChapter(id.value, { name: form.value.name.trim(), sort: form.value.sort })
      uni.showToast({ title: '已更新' })
    } else {
      await createChapter({ subject_id: subjectId.value, name: form.value.name.trim(), sort: form.value.sort })
      uni.showToast({ title: '已添加' })
    }
    setTimeout(() => uni.navigateBack(), 500)
  } catch (e) {
    uni.showToast({ title: e.message || '保存失败', icon: 'none' })
  }
}
</script>

<style scoped>
.page { background: var(--bg-page); min-height: 100vh; padding: 32rpx; }
.form { background: var(--bg-card); border-radius: 24rpx; padding: 32rpx; box-shadow: var(--shadow-card); }
.row { margin-bottom: 32rpx; }
.label { display: block; font-size: 28rpx; color: var(--text-secondary); margin-bottom: 12rpx; }
.input { padding: 24rpx; border: 1rpx solid #eee; border-radius: 12rpx; font-size: 30rpx; color: var(--text); }
.btn { margin-top: 24rpx; padding: 28rpx; border-radius: 24rpx; font-size: 30rpx; }
.primary { background: var(--primary); color: #fff; border: none; }
</style>
