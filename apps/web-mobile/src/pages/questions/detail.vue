<template>
  <view class="page" v-if="q">
    <view class="card img-card" v-if="q.image_url" @click="openImagePreview">
      <CachedImage v-if="imageFullUrl" img-class="img" :src="imageFullUrl" mode="widthFix" @error="onImageError" />
      <view v-else class="img-placeholder">图片加载失败</view>
      <text class="img-tap-hint">点击放大查看</text>
    </view>
    <!-- 调试用：显示图片地址，长按可复制，便于在浏览器中直接打开测试 -->
    <view class="card debug-card" v-if="q.image_url && showDebug">
      <text class="label">调试 - 图片地址</text>
      <text class="debug-url" selectable @longpress="copyImageUrl">{{ imageFullUrl || '(未拼接)' }}</text>
      <text class="debug-hint">长按复制后到浏览器打开，能打开则说明后端正常</text>
    </view>
    <view class="card">
      <text class="label">题目</text>
      <text class="content">{{ q.content }}</text>
    </view>
    <view class="card" v-if="q.analysis">
      <text class="label">解析</text>
      <text class="content">{{ q.analysis }}</text>
    </view>
    <view class="card" v-if="q.answer">
      <text class="label">答案</text>
      <text class="content">{{ q.answer }}</text>
    </view>
    <view class="card notes-card">
      <text class="label">自我剖析</text>
      <textarea
        class="notes-input"
        v-model="userNotes"
        placeholder="记录你的错因、思路或复习笔记…"
        :maxlength="2000"
        @blur="saveUserNotes"
      />
      <view class="notes-actions">
        <button class="btn-save" size="mini" @click="saveUserNotes(true)">保存笔记</button>
      </view>
    </view>
    <view class="meta">创建于 {{ q.created_at }}</view>
    <view class="debug-toggle" @click="showDebug = !showDebug">
      <text class="debug-toggle-text">{{ showDebug ? '隐藏' : '显示' }}调试信息</text>
    </view>
  </view>
  <view class="page empty" v-else-if="!loading">{{ loadFailReason || '加载失败，请返回重试' }}</view>
  <view class="page empty" v-else>加载中...</view>

  <!-- 图片预览：双指捏合 + transform scale，居中显示，比例正确，+/- 有效（与上面 v-if 链无关） -->
  <view class="image-preview-mask" v-if="imagePreviewVisible" @click="closeImagePreview">
    <view
      class="image-preview-area-wrap"
      @click.stop
      @touchstart.capture="onPreviewTouchStart"
      @touchmove.capture="onPreviewTouchMove"
      @touchend.capture="onPreviewTouchEnd"
      @touchcancel.capture="onPreviewTouchEnd"
    >
      <view class="image-preview-inner" :style="previewInnerStyle">
        <CachedImage v-if="imageFullUrl" img-class="image-preview-img" :src="imageFullUrl" mode="widthFix" />
      </view>
    </view>
    <view class="image-preview-toolbar" @click.stop>
      <button class="toolbar-btn" @click.stop="zoomOut">－</button>
      <text class="toolbar-scale">{{ Math.round(imagePreviewScale * 100) }}%</text>
      <button class="toolbar-btn" @click.stop="zoomIn">＋</button>
      <button class="toolbar-close" @click.stop="closeImagePreview">关闭</button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { getQuestion, updateQuestion } from '@/api/questions.js'
import CachedImage from '@/components/CachedImage.vue'
import { API_BASE_URL } from '@/config.js'

const q = ref(null)
const loading = ref(true)
const imageFullUrl = ref('')
const showDebug = ref(false)

/** 加载失败时显示的具体原因，便于排查 */
const loadFailReason = ref('')
const imagePreviewVisible = ref(false)
const imagePreviewScale = ref(1)
const MIN_SCALE = 0.5
const MAX_SCALE = 3
const SCALE_STEP = 0.25
let pinchStartDistance = 0
let pinchStartScale = 1

/** 用 transform 缩放，保持比例；居中显示 */
const previewInnerStyle = computed(() => ({
  transform: `scale(${imagePreviewScale.value})`,
  transformOrigin: 'center center'
}))

const userNotes = ref('')
let saveNotesTimer = null
watch(() => q.value?.image_url, (url) => {
  if (!url || typeof url !== 'string') {
    imageFullUrl.value = ''
    return
  }
  const base = (API_BASE_URL || '').replace(/\/$/, '')
  imageFullUrl.value = url.startsWith('http') ? url : `${base}${url.startsWith('/') ? url : '/' + url}`
  // 调试：控制台输出，便于在微信开发者工具 / vConsole 中查看
  console.log('[错题详情] image_url from API:', url)
  console.log('[错题详情] API_BASE_URL:', API_BASE_URL)
  console.log('[错题详情] imageFullUrl:', imageFullUrl.value)
}, { immediate: true })

watch(() => q.value?.user_notes, (val) => {
  userNotes.value = val ?? ''
}, { immediate: true })

function getTouches(e) {
  const ev = e && (e.mp || e)
  const t = (ev && ev.touches && ev.touches.length) ? ev.touches : (e && e.detail && e.detail.touches) || []
  return Array.isArray(t) ? t : []
}

function getTouchDistance(touches) {
  if (!touches || touches.length < 2) return 0
  const a = touches[0]
  const b = touches[1]
  const ax = a.clientX != null ? a.clientX : (a.pageX != null ? a.pageX : a.x)
  const ay = a.clientY != null ? a.clientY : (a.pageY != null ? a.pageY : a.y)
  const bx = b.clientX != null ? b.clientX : (b.pageX != null ? b.pageX : b.x)
  const by = b.clientY != null ? b.clientY : (b.pageY != null ? b.pageY : b.y)
  return Math.hypot(bx - ax, by - ay)
}

function onPreviewTouchStart(e) {
  const touches = getTouches(e)
  if (touches.length === 2) {
    pinchStartDistance = getTouchDistance(touches)
    pinchStartScale = imagePreviewScale.value
  }
}

function onPreviewTouchMove(e) {
  const touches = getTouches(e)
  if (touches.length === 2) {
    if (pinchStartDistance <= 0) {
      pinchStartDistance = getTouchDistance(touches)
      pinchStartScale = imagePreviewScale.value
    }
    try {
      e.stopPropagation && e.stopPropagation()
      e.preventDefault && e.preventDefault()
    } catch (_) {}
    const d = getTouchDistance(touches)
    if (pinchStartDistance > 0 && d > 0) {
      const scale = (pinchStartScale * d) / pinchStartDistance
      imagePreviewScale.value = Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale))
    }
  }
}

function onPreviewTouchEnd(e) {
  const touches = getTouches(e)
  if (!touches || touches.length < 2) pinchStartDistance = 0
}

function openImagePreview() {
  if (!imageFullUrl.value) return
  imagePreviewScale.value = 1
  pinchStartDistance = 0
  imagePreviewVisible.value = true
}

function closeImagePreview() {
  imagePreviewVisible.value = false
}

function zoomIn() {
  imagePreviewScale.value = Math.min(MAX_SCALE, imagePreviewScale.value + SCALE_STEP)
}

function zoomOut() {
  imagePreviewScale.value = Math.max(MIN_SCALE, imagePreviewScale.value - SCALE_STEP)
}

async function saveUserNotes(immediate = false) {
  if (!q.value?.id) return
  const doSave = async () => {
    const notes = (userNotes.value || '').trim()
    try {
      const updated = await updateQuestion(q.value.id, { user_notes: notes || null })
      if (updated && updated.user_notes !== undefined) q.value.user_notes = updated.user_notes
      uni.showToast({ title: '已保存', icon: 'success' })
    } catch (e) {
      uni.showToast({ title: e.message || '保存失败', icon: 'none' })
    }
  }
  if (immediate) {
    if (saveNotesTimer) clearTimeout(saveNotesTimer)
    saveNotesTimer = null
    await doSave()
    return
  }
  if (saveNotesTimer) clearTimeout(saveNotesTimer)
  saveNotesTimer = setTimeout(doSave, 300)
}

function onImageError(e) {
  console.warn('[错题详情] 图片加载失败', imageFullUrl.value, e)
  imageFullUrl.value = ''
}

function copyImageUrl() {
  if (!imageFullUrl.value) return
  uni.setClipboardData({
    data: imageFullUrl.value,
    success: () => uni.showToast({ title: '已复制到剪贴板', icon: 'none' })
  })
}

onMounted(async () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1]
  const id = parseInt((page.options || {}).id, 10)
  if (!id) {
    loadFailReason.value = '缺少题目 ID，请从错题列表进入'
    loading.value = false
    return
  }
  try {
    q.value = await getQuestion(id)
  } catch (e) {
    loadFailReason.value = e.message || '网络或服务器异常，请返回重试'
    uni.showToast({ title: loadFailReason.value, icon: 'none' })
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page { padding: 32rpx; background: var(--bg-page); min-height: 100vh; }
.card { background: var(--bg-card); border-radius: 24rpx; padding: 28rpx; margin-bottom: 32rpx; box-shadow: var(--shadow-card); }
.label { display: block; font-size: 26rpx; color: var(--text-hint); margin-bottom: 12rpx; }
.content { font-size: 30rpx; color: var(--text); white-space: pre-wrap; word-break: break-all; }
.img-card { position: relative; }
.img { width: 100%; border-radius: 12rpx; }
.img-tap-hint { position: absolute; right: 28rpx; bottom: 16rpx; font-size: 22rpx; color: rgba(255,255,255,0.9); background: rgba(0,0,0,0.4); padding: 8rpx 16rpx; border-radius: 8rpx; }
.meta { font-size: 24rpx; color: var(--text-hint); }
.empty { text-align: center; padding: 60rpx; }
.img-placeholder { padding: 48rpx; text-align: center; color: var(--text-hint); font-size: 28rpx; background: var(--bg-page); border-radius: 12rpx; }

.image-preview-mask { position: fixed; left: 0; top: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.9); z-index: 999; display: flex; flex-direction: column; }
.image-preview-area-wrap { flex: 1; width: 100%; min-height: 0; overflow: auto; -webkit-overflow-scrolling: touch; display: flex; justify-content: center; align-items: center; padding: 40rpx; box-sizing: border-box; }
.image-preview-inner { flex: 0 0 auto; }
.image-preview-img { display: block; width: 100%; }
.image-preview-toolbar { position: absolute; bottom: 0; left: 0; right: 0; padding: 24rpx 32rpx  env(safe-area-inset-bottom); background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; gap: 24rpx; }
.toolbar-btn { width: 72rpx; height: 72rpx; line-height: 72rpx; padding: 0; font-size: 36rpx; color: #fff; background: rgba(255,255,255,0.2); border-radius: 12rpx; }
.toolbar-scale { font-size: 26rpx; color: #fff; min-width: 80rpx; text-align: center; }
.toolbar-close { padding: 16rpx 32rpx; font-size: 28rpx; color: #fff; background: var(--primary); border-radius: 12rpx; }

.notes-card { }
.notes-input { width: 100%; min-height: 160rpx; font-size: 28rpx; color: var(--text); padding: 16rpx; box-sizing: border-box; border: 1rpx solid #eee; border-radius: 12rpx; margin-top: 8rpx; }
.notes-actions { margin-top: 20rpx; }
.btn-save { background: var(--primary); color: #fff; }

.debug-card { background: #fffbe6; }
.debug-url { font-size: 24rpx; color: var(--text-secondary); word-break: break-all; display: block; margin-top: 8rpx; }
.debug-hint { font-size: 22rpx; color: var(--text-hint); display: block; margin-top: 12rpx; }
.debug-toggle { padding: 16rpx; text-align: center; }
.debug-toggle-text { font-size: 24rpx; color: var(--text-hint); }
</style>
