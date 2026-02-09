<template>
  <view class="tabbar">
    <view class="item" :class="{ active: current === 'index' }" @click="go('/pages/index/index')">
      <text class="icon">🏠</text>
      <text class="label" :class="{ active: current === 'index' }">首页</text>
    </view>
    <view class="item" :class="{ active: current === 'questions' }" @click="go('/pages/questions/list')">
      <text class="icon">📚</text>
      <text class="label" :class="{ active: current === 'questions' }">错题本</text>
    </view>
    <view class="item center" @click="onAddTap">
      <view class="camera-btn">
        <text class="camera-icon">📷</text>
      </view>
      <text class="label">添加</text>
    </view>
    <view class="item" :class="{ active: current === 'review' }" @click="go('/pages/review/index')">
      <text class="icon">🔄</text>
      <text class="label" :class="{ active: current === 'review' }">复习</text>
    </view>
    <view class="item" :class="{ active: current === 'my' }" @click="go('/pages/my/index')">
      <text class="icon">👤</text>
      <text class="label" :class="{ active: current === 'my' }">我的</text>
    </view>
  </view>
</template>

<script setup>
import { setSourcePath } from '@/utils/crop-store.js'

defineProps({ current: { type: String, default: '' } })

function go(url) {
  uni.reLaunch({ url })
}

/** 中间添加按钮：根据当前页弹「新建目录」或「拍照添加题目」 */
function onAddTap() {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1]
  const route = (page && (page.route || page.$page?.route)) || ''
  const opts = (page && (page.options || page.$page?.options)) || {}
  const isInChapters = route.includes('chapters/list') || route.includes('chapters/questions')
  const subjectId = opts.subject_id || ''
  const subjectName = opts.subject_name ? decodeURIComponent(opts.subject_name) : ''

  if (isInChapters) {
    uni.showActionSheet({
      itemList: ['新建章节目录', '拍照添加题目'],
      success: (res) => {
        if (res.tapIndex === 0) {
          if (subjectId) {
            uni.navigateTo({
              url: `/pages/chapters/edit?subject_id=${subjectId}&subject_name=${encodeURIComponent(subjectName)}`
            })
          } else {
            uni.showToast({ title: '请先进入一个错题本', icon: 'none' })
          }
        } else if (res.tapIndex === 1) {
          uni.chooseImage({
            count: 1,
            sourceType: ['camera'],
            success: (imgRes) => {
              setSourcePath(imgRes.tempFilePaths[0])
              uni.navigateTo({ url: '/pages/common/image-crop' })
            }
          })
        }
      }
    })
  } else {
    uni.showActionSheet({
      itemList: ['新建错题本', '拍照添加题目'],
      success: (res) => {
        if (res.tapIndex === 0) {
          go('/pages/subjects/create-with-photo')
        } else if (res.tapIndex === 1) {
          go('/pages/questions/list?openCamera=1')
        }
      }
    })
  }
}
</script>

<style scoped>
.tabbar {
  --tab-primary: #4A90E2;
  --tab-primary-light: #66B2FF;
}
.tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 120rpx;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-around;
  box-shadow: 0 -2rpx 16rpx rgba(0,0,0,0.05);
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 100;
}
.item { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; }
.icon { font-size: 40rpx; color: #999; }
.item:not(.center) .icon { transition: color 0.2s; }
.item:not(.center).active .icon { color: var(--tab-primary); }
.item.center .label { color: #999; }
.label { font-size: 22rpx; color: #999; margin-top: 4rpx; transition: color 0.2s, font-weight 0.2s; }
.label.active { color: var(--tab-primary); font-weight: 600; }
.item.center .camera-btn {
  width: 96rpx; height: 96rpx;
  background: linear-gradient(135deg, var(--tab-primary) 0%, #3a7bc8 100%);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin-top: -40rpx;
  box-shadow: 0 8rpx 24rpx rgba(74,144,226,0.35);
}
.item.center .camera-btn:active { background: linear-gradient(135deg, var(--tab-primary-light) 0%, var(--tab-primary) 100%); }
.item.center .camera-icon { font-size: 44rpx; }
</style>
