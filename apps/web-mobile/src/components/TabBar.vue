<template>
  <view class="tabbar">
    <view class="item" :class="{ active: current === 'index' }" @click="go('/pages/index/index')">
      <image class="icon-img" :src="iconDataUri('home', current === 'index')" mode="aspectFit" />
      <text class="label" :class="{ active: current === 'index' }">首页</text>
    </view>
    <view class="item" :class="{ active: current === 'questions' }" @click="go('/pages/questions/list')">
      <image class="icon-img" :src="iconDataUri('book', current === 'questions')" mode="aspectFit" />
      <text class="label" :class="{ active: current === 'questions' }">错题本</text>
    </view>
    <view class="item center" @click="onAddTap">
      <view class="camera-btn">
        <image class="camera-icon-img" :src="iconDataUri('add', true)" mode="aspectFit" />
      </view>
      <text class="label">添加</text>
    </view>
    <view class="item" :class="{ active: current === 'review' }" @click="go('/pages/review/index')">
      <image class="icon-img" :src="iconDataUri('review', current === 'review')" mode="aspectFit" />
      <text class="label" :class="{ active: current === 'review' }">复习</text>
    </view>
    <view class="item" :class="{ active: current === 'my' }" @click="go('/pages/my/index')">
      <image class="icon-img" :src="iconDataUri('user', current === 'my')" mode="aspectFit" />
      <text class="label" :class="{ active: current === 'my' }">我的</text>
    </view>
  </view>
</template>

<script setup>
import { setSourcePath } from '@/utils/crop-store.js'

defineProps({ current: { type: String, default: '' } })

const COLOR_NORMAL = '#999'
const COLOR_ACTIVE = '#4A90E2'
const COLOR_WHITE = '#fff'

const lineIcons = {
  home: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
  book: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><line x1="12" y1="6" x2="16" y2="6"/><line x1="12" y1="10" x2="16" y2="10"/></svg>',
  add: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>',
  review: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>',
  user: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
}

function iconDataUri(name, active) {
  const svg = (lineIcons[name] || '').replace(/C/g, name === 'add' ? COLOR_WHITE : (active ? COLOR_ACTIVE : COLOR_NORMAL))
  return 'data:image/svg+xml,' + encodeURIComponent(svg)
}

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
      itemList: ['新建章节目录', '拍照添加题目', '手动添加题目'],
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
            sourceType: ['album', 'camera'],
            success: (imgRes) => {
              setSourcePath(imgRes.tempFilePaths[0])
              uni.navigateTo({ url: '/pages/common/image-crop' })
            }
          })
        } else if (res.tapIndex === 2) {
          uni.navigateTo({
            url: `/pages/questions/add?mode=manual&subject_id=${subjectId}&subject_name=${encodeURIComponent(subjectName)}`
          })
        }
      }
    })
  } else {
    uni.showActionSheet({
      itemList: ['新建错题本', '拍照添加题目', '手动添加题目'],
      success: (res) => {
        if (res.tapIndex === 0) {
          go('/pages/subjects/create-with-photo')
        } else if (res.tapIndex === 1) {
          go('/pages/questions/list?openCamera=1')
        } else if (res.tapIndex === 2) {
          uni.navigateTo({ url: '/pages/questions/add?mode=manual' })
        }
      }
    })
  }
}
</script>

<style scoped>
.tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 120rpx;
  background: var(--bg-card);
  display: flex;
  align-items: center;
  justify-content: space-around;
  box-shadow: 0 -4rpx 20rpx rgba(0,0,0,0.06);
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 100;
}
.item { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; }
.icon-img { width: 44rpx; height: 44rpx; }
.item.center .label { color: var(--text-hint); }
.label { font-size: 22rpx; color: var(--text-hint); margin-top: 4rpx; transition: color 0.2s, font-weight 0.2s; }
.label.active { color: var(--primary); font-weight: 600; }
.item.center .camera-btn {
  width: 96rpx; height: 96rpx;
  background: linear-gradient(135deg, var(--primary) 0%, #3a7bc8 100%);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin-top: -40rpx;
  box-shadow: 0 8rpx 24rpx rgba(74,144,226,0.35);
}
.item.center .camera-btn:active { background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary) 100%); }
.camera-icon-img { width: 48rpx; height: 48rpx; }
</style>
