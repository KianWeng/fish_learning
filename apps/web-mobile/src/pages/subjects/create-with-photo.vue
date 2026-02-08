<template>
  <view class="page">
    <view class="section">
      <view class="field">
        <text class="label">错题本名称</text>
        <input class="input" v-model="form.name" placeholder="请输入错题本名称" />
      </view>
      <view class="field">
        <text class="label">封面照片</text>
        <text class="hint">拍照或从相册选择，作为错题本封面</text>
        <view v-if="!imageUrl" class="upload-area" @click="chooseImage">
          <text class="upload-icon">📷</text>
          <text class="upload-text">选择照片 / 拍照</text>
        </view>
        <view v-else class="preview-wrap">
          <image :src="imageFullUrl" mode="aspectFill" class="preview-img" />
          <view class="preview-remove" @click="removeImage">更换封面</view>
        </view>
      </view>
      <button class="btn primary" @click="submit" :disabled="saving">创建错题本</button>
    </view>
    <view class="tabbar-placeholder" />
    <TabBar current="" />
  </view>
</template>

<script setup>
import { ref, watch } from 'vue'
import TabBar from '@/components/TabBar.vue'
import { API_BASE_URL } from '@/config.js'
import { createSubject } from '@/api/subjects.js'
import { uploadImage } from '@/api/questions.js'

const form = ref({ name: '' })
const imageUrl = ref('')
const imageFullUrl = ref('')
const saving = ref(false)

watch(imageUrl, (url) => {
  imageFullUrl.value = url ? (url.startsWith('http') ? url : API_BASE_URL + url) : ''
})

function chooseImage() {
  uni.chooseImage({
    count: 1,
    sourceType: ['album', 'camera'],
    success: async (res) => {
      const path = res.tempFilePaths[0]
      uni.showLoading({ title: '上传中...' })
      try {
        const data = await uploadImage(path)
        uni.hideLoading()
        imageUrl.value = data.url || ''
      } catch (e) {
        uni.hideLoading()
        uni.showToast({ title: e.message || '上传失败', icon: 'none' })
      }
    }
  })
}

function removeImage() {
  imageUrl.value = ''
}

async function submit() {
  const name = form.value.name.trim()
  if (!name) {
    uni.showToast({ title: '请输入错题本名称', icon: 'none' })
    return
  }
  saving.value = true
  try {
    await createSubject({
      name,
      sort: 0,
      cover_url: imageUrl.value || undefined
    })
    uni.showToast({ title: '已创建' })
    setTimeout(() => uni.navigateBack(), 500)
  } catch (e) {
    uni.showToast({ title: e.message || '创建失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.page { padding: 24rpx 24rpx 140rpx; min-height: 100vh; background: #f5f6fa; }
.section { background: #fff; border-radius: 20rpx; padding: 32rpx; box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.06); }
.field { margin-bottom: 32rpx; }
.label { display: block; font-size: 28rpx; color: #333; margin-bottom: 8rpx; font-weight: 500; }
.hint { display: block; font-size: 24rpx; color: #999; margin-bottom: 16rpx; }
.input {
  width: 100%;
  padding: 24rpx;
  border: 1rpx solid #e5e7eb;
  border-radius: 12rpx;
  font-size: 30rpx;
  box-sizing: border-box;
}
.upload-area {
  padding: 56rpx 32rpx;
  border: 2rpx dashed #d1d5db;
  border-radius: 16rpx;
  text-align: center;
  background: #fafafa;
}
.upload-icon { display: block; font-size: 56rpx; margin-bottom: 12rpx; }
.upload-text { font-size: 28rpx; color: #6b7280; }
.preview-wrap { border-radius: 16rpx; overflow: hidden; background: #f5f5f5; }
.preview-img { width: 100%; height: 320rpx; display: block; }
.preview-remove { margin-top: 16rpx; font-size: 28rpx; color: #1989fa; text-align: center; }
.btn { margin-top: 24rpx; padding: 28rpx; border-radius: 12rpx; font-size: 30rpx; width: 100%; }
.primary { background: #07c160; color: #fff; border: none; }
.tabbar-placeholder { height: 120rpx; }
</style>
