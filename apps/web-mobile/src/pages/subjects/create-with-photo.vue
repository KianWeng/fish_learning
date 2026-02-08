<template>
  <view class="page">
    <view class="section">
      <view class="field">
        <text class="label">错题本名称</text>
        <input class="input" v-model="form.name" placeholder="请输入错题本名称" />
      </view>
      <view class="field">
        <text class="label">题目（可选）</text>
        <textarea class="textarea" v-model="form.content" placeholder="可手动输入题目内容" />
      </view>
      <view class="field">
        <text class="label">解析（可选）</text>
        <textarea class="textarea" v-model="form.analysis" placeholder="解析" />
      </view>
      <view class="field">
        <text class="label">答案（可选）</text>
        <input class="input" v-model="form.answer" placeholder="答案" />
      </view>
      <view class="field">
        <text class="label">上传照片（可选）</text>
        <view v-if="!imageUrl" class="upload-area" @click="chooseImage">
          <text class="upload-icon">📷</text>
          <text class="upload-text">选择照片 / 拍照</text>
        </view>
        <view v-else class="preview-wrap">
          <image :src="imageFullUrl" mode="widthFix" class="preview-img" />
          <view class="preview-remove" @click="removeImage">移除</view>
        </view>
      </view>
      <view class="tip">仅填名称可创建空错题本；填写题目或上传照片会同时添加第一道错题</view>
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
import { createQuestion, uploadImage } from '@/api/questions.js'

const form = ref({ name: '', content: '', analysis: '', answer: '' })
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
  const hasContent = form.value.content.trim() || imageUrl.value
  saving.value = true
  try {
    const subject = await createSubject({ name, sort: 0 })
    const subjectId = subject.id
    if (hasContent) {
      const content = form.value.content.trim() || '（见图片）'
      await createQuestion({
        subject_id: subjectId,
        chapter_id: undefined,
        content,
        analysis: form.value.analysis.trim() || undefined,
        answer: form.value.answer.trim() || undefined,
        image_url: imageUrl.value || undefined,
        source: 'photo'
      })
    }
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
.section { background: #fff; border-radius: 12rpx; padding: 32rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06); }
.field { margin-bottom: 24rpx; }
.label { display: block; font-size: 28rpx; color: #666; margin-bottom: 8rpx; }
.input { width: 100%; padding: 24rpx; border: 1rpx solid #eee; border-radius: 8rpx; font-size: 30rpx; box-sizing: border-box; }
.textarea { width: 100%; min-height: 120rpx; padding: 20rpx; border: 1rpx solid #eee; border-radius: 8rpx; font-size: 28rpx; box-sizing: border-box; }
.upload-area { padding: 48rpx; border: 2rpx dashed #ddd; border-radius: 12rpx; text-align: center; background: #fafafa; }
.upload-icon { display: block; font-size: 56rpx; margin-bottom: 12rpx; }
.upload-text { font-size: 28rpx; color: #999; }
.preview-wrap { position: relative; }
.preview-img { width: 100%; border-radius: 8rpx; }
.preview-remove { margin-top: 12rpx; font-size: 26rpx; color: #1989fa; }
.tip { font-size: 24rpx; color: #999; margin-bottom: 24rpx; }
.btn { margin-top: 16rpx; padding: 28rpx; border-radius: 12rpx; font-size: 30rpx; width: 100%; }
.primary { background: #07c160; color: #fff; border: none; }
.tabbar-placeholder { height: 120rpx; }
</style>
