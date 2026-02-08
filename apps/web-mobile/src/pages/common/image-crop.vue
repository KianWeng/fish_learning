<template>
  <view class="page">
    <view class="image-wrap" id="imageWrap" :style="{ width: displayW + 'px' }">
      <image
        v-if="sourcePath"
        :src="sourcePath"
        class="crop-image"
        :style="{ width: displayW + 'px' }"
        mode="widthFix"
        @load="onImageLoad"
      />
      <!-- 半透明遮罩 + 镂空裁剪框 -->
      <view
        v-if="imageLoaded"
        class="overlay"
        @touchstart="onOverlayTouchStart"
        @touchmove.prevent="onOverlayTouchMove"
        @touchend="onOverlayTouchEnd"
      >
        <!-- 上下左右四块遮罩，中间镂空即裁剪区 -->
        <view class="mask top" :style="{ height: boxY + 'px' }" />
        <view class="mask bottom" :style="{ top: (boxY + boxH) + 'px', height: (displayH - boxY - boxH) + 'px' }" />
        <view class="mask left" :style="{ top: boxY + 'px', left: 0, width: boxX + 'px', height: boxH + 'px' }" />
        <view class="mask right" :style="{ top: boxY + 'px', left: (boxX + boxW) + 'px', width: (displayW - boxX - boxW) + 'px', height: boxH + 'px' }" />
        <!-- 裁剪框边框 -->
        <view
          class="crop-box"
          :style="cropBoxStyle"
        >
          <!-- 四角拖拽手柄 -->
          <view class="handle tl" data-handle="tl" />
          <view class="handle tr" data-handle="tr" />
          <view class="handle bl" data-handle="bl" />
          <view class="handle br" data-handle="br" />
        </view>
      </view>
    </view>
    <view class="tips">拖动裁剪框移动，拖拽四角调整大小</view>
    <view class="actions">
      <button class="btn cancel" @click="cancel">取消</button>
      <button class="btn confirm" @click="confirm">使用此图</button>
    </view>
    <canvas
      canvas-id="cropCanvas"
      class="hidden-canvas"
      :style="{ width: (displayW || 750) + 'px', height: (displayH || 1000) + 'px' }"
    />
  </view>
</template>

<script setup>
import { ref, computed, onMounted, getCurrentInstance, nextTick } from 'vue'
import { getSourcePath, setResultPath, clear } from '@/utils/crop-store.js'

const instance = getCurrentInstance()
const sourcePath = ref('')
const imgW = ref(0)
const imgH = ref(0)
const displayW = ref(0)
const displayH = ref(0)
const imageLoaded = ref(false)
const wrapRect = ref({ left: 0, top: 0, width: 0, height: 0 })

// 裁剪框（相对图片展示区域的像素）
const boxX = ref(0)
const boxY = ref(0)
const boxW = ref(0)
const boxH = ref(0)

const MIN_BOX = 60
const HANDLE_SIZE = 44

let touchMode = '' // 'move' | 'tl' | 'tr' | 'bl' | 'br'
let startX = 0
let startY = 0
let startBoxX = 0
let startBoxY = 0
let startBoxW = 0
let startBoxH = 0

const cropBoxStyle = computed(() => ({
  left: boxX.value + 'px',
  top: boxY.value + 'px',
  width: boxW.value + 'px',
  height: boxH.value + 'px'
}))

function getWrapRect() {
  return new Promise((resolve) => {
    nextTick(() => {
      const query = uni.createSelectorQuery().in(instance)
      query.select('#imageWrap').boundingClientRect((rect) => {
        if (rect) {
          wrapRect.value = { left: rect.left, top: rect.top, width: rect.width, height: rect.height }
          resolve(rect)
        } else resolve(null)
      }).exec()
    })
  })
}

function onImageLoad(e) {
  const { width, height } = e.detail
  imgW.value = width
  imgH.value = height
  const sysInfo = uni.getSystemInfoSync()
  const w = sysInfo.windowWidth || 375
  displayW.value = w
  displayH.value = Math.round(height * (w / width))
  imageLoaded.value = true
  getWrapRect().then(() => {
    boxX.value = Math.round(displayW.value * 0.1)
    boxY.value = Math.round(displayH.value * 0.1)
    boxW.value = Math.round(displayW.value * 0.8)
    boxH.value = Math.round(displayH.value * 0.8)
    clampBox()
  })
}

function clampBox() {
  const x = Math.max(0, Math.min(displayW.value - MIN_BOX, boxX.value))
  const y = Math.max(0, Math.min(displayH.value - MIN_BOX, boxY.value))
  const w = Math.max(MIN_BOX, Math.min(displayW.value - x, boxW.value))
  const h = Math.max(MIN_BOX, Math.min(displayH.value - y, boxH.value))
  boxX.value = x
  boxY.value = y
  boxW.value = w
  boxH.value = h
}

function hitHandle(clientX, clientY) {
  const { left, top } = wrapRect.value
  const lx = clientX - left
  const ly = clientY - top
  const x = boxX.value
  const y = boxY.value
  const w = boxW.value
  const h = boxH.value
  const s = HANDLE_SIZE
  if (lx >= x && lx <= x + s && ly >= y && ly <= y + s) return 'tl'
  if (lx >= x + w - s && lx <= x + w && ly >= y && ly <= y + s) return 'tr'
  if (lx >= x && lx <= x + s && ly >= y + h - s && ly <= y + h) return 'bl'
  if (lx >= x + w - s && lx <= x + w && ly >= y + h - s && ly <= y + h) return 'br'
  if (lx >= x + s && lx <= x + w - s && ly >= y + s && ly <= y + h - s) return 'move'
  return ''
}

function onOverlayTouchStart(e) {
  if (!e.touches || !e.touches[0]) return
  const clientX = e.touches[0].clientX
  const clientY = e.touches[0].clientY
  getWrapRect()
  touchMode = hitHandle(clientX, clientY)
  startX = clientX
  startY = clientY
  startBoxX = boxX.value
  startBoxY = boxY.value
  startBoxW = boxW.value
  startBoxH = boxH.value
}

function onOverlayTouchMove(e) {
  if (!e.touches || !e.touches[0]) return
  const clientX = e.touches[0].clientX
  const clientY = e.touches[0].clientY
  const dx = clientX - startX
  const dy = clientY - startY

  if (touchMode === 'move') {
    boxX.value = Math.max(0, Math.min(displayW.value - boxW.value, startBoxX + dx))
    boxY.value = Math.max(0, Math.min(displayH.value - boxH.value, startBoxY + dy))
    return
  }

  if (touchMode === 'tl') {
    let nx = startBoxX + dx
    let ny = startBoxY + dy
    let nw = startBoxW - dx
    let nh = startBoxH - dy
    if (nw < MIN_BOX) { nx = startBoxX + startBoxW - MIN_BOX; nw = MIN_BOX }
    if (nh < MIN_BOX) { ny = startBoxY + startBoxH - MIN_BOX; nh = MIN_BOX }
    boxX.value = Math.max(0, nx)
    boxY.value = Math.max(0, ny)
    boxW.value = Math.min(displayW.value - boxX.value, nw)
    boxH.value = Math.min(displayH.value - boxY.value, nh)
    return
  }
  if (touchMode === 'tr') {
    let nw = startBoxW + dx
    let nh = startBoxH - dy
    if (nw < MIN_BOX) nw = MIN_BOX
    if (nh < MIN_BOX) nh = MIN_BOX
    boxY.value = Math.max(0, Math.min(displayH.value - MIN_BOX, startBoxY + dy))
    boxW.value = Math.max(MIN_BOX, Math.min(displayW.value - boxX.value, nw))
    boxH.value = Math.max(MIN_BOX, Math.min(displayH.value - boxY.value, nh))
    return
  }
  if (touchMode === 'bl') {
    let nx = startBoxX + dx
    let nw = startBoxW - dx
    let nh = startBoxH + dy
    if (nw < MIN_BOX) { nx = startBoxX + startBoxW - MIN_BOX; nw = MIN_BOX }
    if (nh < MIN_BOX) nh = MIN_BOX
    boxX.value = Math.max(0, Math.min(displayW.value - MIN_BOX, nx))
    boxW.value = Math.max(MIN_BOX, Math.min(displayW.value - boxX.value, nw))
    boxH.value = Math.max(MIN_BOX, Math.min(displayH.value - boxY.value, nh))
    return
  }
  if (touchMode === 'br') {
    let nw = startBoxW + dx
    let nh = startBoxH + dy
    boxW.value = Math.max(MIN_BOX, Math.min(displayW.value - boxX.value, nw))
    boxH.value = Math.max(MIN_BOX, Math.min(displayH.value - boxY.value, nh))
  }
}

function onOverlayTouchEnd() {
  touchMode = ''
}

function cancel() {
  clear()
  uni.navigateBack()
}

function getCropRect() {
  const outW = Math.round(boxW.value)
  const outH = Math.round(boxH.value)
  return {
    drawFullThenCrop: true,
    boxX: boxX.value,
    boxY: boxY.value,
    boxW: outW,
    boxH: outH,
    displayW: displayW.value,
    displayH: displayH.value,
    fwPx: outW,
    fhPx: outH
  }
}

function confirm() {
  if (!sourcePath.value || !imageLoaded.value || !imgW.value) {
    uni.showToast({ title: '请等待图片加载', icon: 'none' })
    return
  }
  const rect = getCropRect()
  const w = Math.round(rect.fwPx)
  const h = Math.round(rect.fhPx)

  // #ifdef H5
  exportH5(rect, w, h)
  // #endif
  // #ifndef H5
  exportMiniProgram(rect, w, h)
  // #endif
}

function exportMiniProgram(rect, outW, outH) {
  uni.showLoading({ title: '生成中...' })
  const ctx = uni.createCanvasContext('cropCanvas', instance)
  const { boxX, boxY, boxW, boxH, displayW, displayH } = rect
  ctx.drawImage(sourcePath.value, 0, 0, displayW, displayH)
  ctx.draw(false, () => {
    setTimeout(() => {
      uni.canvasToTempFilePath({
        canvasId: 'cropCanvas',
        x: boxX,
        y: boxY,
        width: boxW,
        height: boxH,
        destWidth: outW * 2,
        destHeight: outH * 2,
        fileType: 'jpg',
        success: (r) => {
          uni.hideLoading()
          setResultPath(r.tempFilePath)
          uni.navigateBack()
        },
        fail: (err) => {
          uni.hideLoading()
          uni.showToast({ title: '生成失败', icon: 'none' })
          console.error(err)
        }
      }, instance)
    }, 350)
  })
}

function exportH5(rect, outW, outH) {
  const { boxX, boxY, boxW, boxH, displayW, displayH } = rect
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    const full = document.createElement('canvas')
    full.width = displayW
    full.height = displayH
    const ctxFull = full.getContext('2d')
    ctxFull.drawImage(img, 0, 0, displayW, displayH)
    const crop = document.createElement('canvas')
    crop.width = outW
    crop.height = outH
    const ctxCrop = crop.getContext('2d')
    ctxCrop.drawImage(full, boxX, boxY, boxW, boxH, 0, 0, outW, outH)
    crop.toBlob((blob) => {
      const url = URL.createObjectURL(blob)
      setResultPath(url)
      uni.navigateBack()
    }, 'image/jpeg', 0.9)
  }
  img.onerror = () => uni.showToast({ title: '图片加载失败', icon: 'none' })
  img.src = sourcePath.value
}

onMounted(() => {
  sourcePath.value = getSourcePath()
  if (!sourcePath.value) {
    uni.showToast({ title: '未选择图片', icon: 'none' })
    setTimeout(() => uni.navigateBack(), 500)
  }
})
</script>

<script>
export default {
  name: 'ImageCrop'
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #111;
  padding: 24rpx;
  box-sizing: border-box;
}
.image-wrap {
  position: relative;
  margin: 0 auto;
  overflow: hidden;
  border-radius: 16rpx;
  background: #333;
}
.crop-image {
  display: block;
  vertical-align: top;
}
.overlay {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
}
.mask {
  position: absolute;
  left: 0;
  width: 100%;
  background: rgba(0, 0, 0, 0.5);
}
.mask.top {
  top: 0;
}
.mask.left,
.mask.right {
  width: auto;
  height: auto;
}
.crop-box {
  position: absolute;
  border: 4rpx solid #07c160;
  border-radius: 8rpx;
  box-sizing: border-box;
}
.handle {
  position: absolute;
  width: 44rpx;
  height: 44rpx;
  background: rgba(7, 193, 96, 0.3);
  border: 4rpx solid #07c160;
  border-radius: 8rpx;
  box-sizing: border-box;
}
.handle.tl { top: -4rpx; left: -4rpx; }
.handle.tr { top: -4rpx; right: -4rpx; }
.handle.bl { bottom: -4rpx; left: -4rpx; }
.handle.br { bottom: -4rpx; right: -4rpx; }
.tips {
  color: #999;
  font-size: 26rpx;
  text-align: center;
  margin-top: 24rpx;
}
.actions {
  display: flex;
  gap: 24rpx;
  margin-top: 48rpx;
  padding: 0 24rpx;
}
.btn {
  flex: 1;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 12rpx;
  font-size: 30rpx;
  border: none;
}
.cancel {
  background: #444;
  color: #fff;
}
.confirm {
  background: #07c160;
  color: #fff;
}
.hidden-canvas {
  position: fixed;
  left: -9999px;
  top: 0;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}
</style>
