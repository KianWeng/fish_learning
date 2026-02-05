<template>
  <view class="page">
    <view class="form">
      <view class="row">
        <text class="label">科目名称</text>
        <input class="input" v-model="form.name" placeholder="请输入科目名称" />
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
import { createSubject, updateSubject } from '@/api/subjects.js'

const id = ref(null)
const form = ref({ name: '', sort: 0 })

onMounted(() => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1]
  const opts = page.options || {}
  if (opts.id) {
    id.value = parseInt(opts.id, 10)
    form.value.name = opts.name ? decodeURIComponent(opts.name) : ''
    form.value.sort = parseInt(opts.sort, 10) || 0
  }
})

async function submit() {
  if (!form.value.name.trim()) {
    uni.showToast({ title: '请输入科目名称', icon: 'none' })
    return
  }
  try {
    if (id.value) {
      await updateSubject(id.value, { name: form.value.name.trim(), sort: form.value.sort })
      uni.showToast({ title: '已更新' })
    } else {
      await createSubject({ name: form.value.name.trim(), sort: form.value.sort })
      uni.showToast({ title: '已添加' })
    }
    setTimeout(() => uni.navigateBack(), 500)
  } catch (e) {
    uni.showToast({ title: e.message || '保存失败', icon: 'none' })
  }
}
</script>

<style scoped>
.page { padding: 24rpx; }
.form { background: #fff; border-radius: 12rpx; padding: 32rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06); }
.row { margin-bottom: 32rpx; }
.label { display: block; font-size: 28rpx; color: #666; margin-bottom: 12rpx; }
.input { padding: 24rpx; border: 1rpx solid #eee; border-radius: 8rpx; font-size: 30rpx; }
.btn { margin-top: 24rpx; padding: 28rpx; border-radius: 12rpx; font-size: 30rpx; }
.primary { background: #07c160; color: #fff; border: none; }
</style>
