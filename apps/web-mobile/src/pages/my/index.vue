<template>
  <view class="page">
    <view class="profile">
      <view class="avatar-wrap" @click="goLoginIfNeed">
        <CachedImage v-if="displayAvatarUrl" img-class="avatar-img" :src="displayAvatarUrl" mode="aspectFill" img-style="width: 100%; height: 100%; display: block;" />
        <text v-else class="avatar-placeholder">👤</text>
      </view>
      <text class="nickname">{{ userInfo.nickname || (isLoggedIn ? '微信用户' : '未登录') }}</text>
      <text class="desc" v-if="userInfo.desc">{{ userInfo.desc }}</text>
      <view class="auth-row">
        <button v-if="!isLoggedIn" class="btn-auth" @click="goLogin">去登录</button>
        <button v-else class="btn-auth secondary" @click="logout">退出登录</button>
      </view>
    </view>

    <view class="menu">
      <view class="menu-item" @click="goStats">
        <text class="menu-icon">📊</text>
        <text class="menu-text">数据统计</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="goSubjects">
        <text class="menu-icon">📁</text>
        <text class="menu-text">科目管理</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="goPdfManage">
        <text class="menu-icon">📄</text>
        <text class="menu-text">PDF 管理</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <view class="storage-card">
      <view class="storage-header">
        <text class="storage-label">存储空间</text>
        <button class="btn-clear-cache" size="mini" @click="refreshStorage">刷新</button>
      </view>
      <view class="storage-progress-wrap" v-if="storageLimitNum > 0">
        <view class="storage-progress-track">
          <view class="storage-progress-fill" :style="{ width: storagePercent + '%' }" />
        </view>
      </view>
      <text class="storage-value">{{ storageText }}</text>
      <text class="storage-debug" v-if="storageDebugText">{{ storageDebugText }}</text>
    </view>

    <view class="tabbar-placeholder" />
    <TabBar current="my" />
  </view>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import TabBar from '@/components/TabBar.vue'
import CachedImage from '@/components/CachedImage.vue'
import request from '@/api/request.js'
import { API_BASE_URL } from '@/config.js'

const userInfo = ref({ nickname: '', desc: '', avatar_url: '' })
const token = ref('')

/** 云端存储（字节）：登录后从 GET /auth/storage 拉取，默认 100MB */
const storageCloudUsedBytes = ref(0)
const storageCloudLimitBytes = ref(0)
/** 本地缓存：uni.getStorageInfoSync()，单位 KB，小程序约 10MB 上限 */
const storageLocalUsedKB = ref(0)
const storageLocalLimitKB = ref(0)
/** 显示用：优先云端，未登录或接口失败时用本地 */
const storageUsedNum = computed(() =>
  storageCloudLimitBytes.value > 0
    ? storageCloudUsedBytes.value / 1024
    : storageLocalUsedKB.value
)
const storageLimitNum = computed(() =>
  storageCloudLimitBytes.value > 0
    ? storageCloudLimitBytes.value / 1024
    : storageLocalLimitKB.value
)

const storagePercent = computed(() => {
  const limit = storageLimitNum.value
  if (limit <= 0) return 0
  const used = storageUsedNum.value
  return Math.min(100, Math.round((used / limit) * 100))
})

const storageText = computed(() => {
  const used = storageUsedNum.value
  const limit = storageLimitNum.value
  const usedStr = (used / 1024).toFixed(2) + ' MB'
  if (limit > 0) {
    const remain = (limit - used) / 1024
    return `已用 ${usedStr}，剩余 ${remain.toFixed(2)} MB`
  }
  return `已用 ${usedStr}`
})

/** 调试：数据来源与原始值，便于排查 10MB 显示问题 */
const storageDebugText = computed(() => {
  if (storageCloudLimitBytes.value > 0) {
    return `来源: 云端 | limit_bytes=${storageCloudLimitBytes.value} used_bytes=${storageCloudUsedBytes.value}`
  }
  return `来源: 本地缓存 | limitSize=${storageLocalLimitKB.value}KB currentSize=${storageLocalUsedKB.value}KB`
})

const isLoggedIn = computed(() => !!token.value)

/** 头像完整 URL：相对路径时拼接 API 基地址，否则小程序/H5 会请求错域名 */
const displayAvatarUrl = computed(() => {
  const url = userInfo.value.avatar_url
  if (!url || typeof url !== 'string') return ''
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  const base = API_BASE_URL.replace(/\/$/, '')
  return base + (url.startsWith('/') ? url : '/' + url)
})

watch(displayAvatarUrl, (v) => {
  console.log('[我的页] displayAvatarUrl 当前值:', v || '(空)')
}, { immediate: true })

onMounted(() => {
  try {
    token.value = uni.getStorageSync('token') || ''
    const u = uni.getStorageSync('user')
    console.log('[我的页] onMounted token=', !!token.value, 'storage user=', u, 'avatar_url=', u?.avatar_url)
    if (u && typeof u === 'object') {
      userInfo.value.nickname = u.nickname || ''
      userInfo.value.avatar_url = u.avatar_url || ''
    }
    if (!userInfo.value.nickname) {
      const nick = uni.getStorageSync('user_nickname')
      if (nick) userInfo.value.nickname = nick
    }
    const desc = uni.getStorageSync('user_desc')
    if (desc) userInfo.value.desc = desc
    console.log('[我的页] 从 storage 还原后 userInfo.avatar_url=', userInfo.value.avatar_url)
  } catch (e) {
    console.warn('[我的页] onMounted 读 storage 异常', e)
  }
  if (token.value) fetchUser()
  refreshStorage()
})

function refreshStorage() {
  try {
    const info = uni.getStorageInfoSync()
    storageLocalUsedKB.value = info.currentSize ?? 0
    storageLocalLimitKB.value = info.limitSize ?? 0
    console.log('[我的页] 本地缓存 getStorageInfoSync:', {
      currentSize: info.currentSize,
      limitSize: info.limitSize,
      keys: (info.keys || []).length
    })
  } catch (e) {
    storageLocalUsedKB.value = 0
    storageLocalLimitKB.value = 0
    console.warn('[我的页] getStorageInfoSync 失败', e)
  }
  if (token.value) fetchCloudStorage()
}

async function fetchCloudStorage() {
  if (!token.value) return
  try {
    const res = await request.get('/auth/storage')
    storageCloudUsedBytes.value = res.used_bytes ?? 0
    storageCloudLimitBytes.value = res.limit_bytes ?? 0
    console.log('[我的页] 云端存储 /auth/storage:', {
      limit_bytes: res.limit_bytes,
      used_bytes: res.used_bytes,
      limit_MB: (res.limit_bytes || 0) / (1024 * 1024),
      used_MB: (res.used_bytes || 0) / (1024 * 1024)
    })
  } catch (e) {
    console.warn('[我的页] /auth/storage 失败，使用本地缓存显示', e)
    storageCloudUsedBytes.value = 0
    storageCloudLimitBytes.value = 0
  }
}

async function fetchUser() {
  try {
    const u = await request.get('/auth/me')
    console.log('[我的页] /auth/me 响应:', u, 'avatar_url=', u?.avatar_url)
    userInfo.value.nickname = u.nickname || userInfo.value.nickname
    userInfo.value.avatar_url = u.avatar_url || ''
    uni.setStorageSync('user', u)
    await fetchCloudStorage()
    console.log('[我的页] fetchUser 后 userInfo.avatar_url=', userInfo.value.avatar_url, 'displayAvatarUrl 将使用 API_BASE_URL=', API_BASE_URL)
  } catch (e) {
    console.warn('[我的页] fetchUser 失败', e)
  }
}

function goLogin() {
  uni.navigateTo({ url: '/pages/auth/login' })
}

function goLoginIfNeed() {
  if (!isLoggedIn.value) goLogin()
}

function logout() {
  uni.removeStorageSync('token')
  uni.removeStorageSync('user')
  token.value = ''
  userInfo.value = { nickname: '', desc: '', avatar_url: '' }
  uni.showToast({ title: '已退出', icon: 'none' })
}

function goStats() {
  uni.navigateTo({ url: '/pages/stats/index' })
}

function goSubjects() {
  uni.navigateTo({ url: '/pages/subjects/list' })
}

function goPdfManage() {
  uni.navigateTo({ url: '/pages/import/pdf-manage' })
}
</script>

<style scoped>
.page { padding: 32rpx 32rpx 140rpx; background: var(--bg-page); min-height: 100vh; }
.profile {
  background: var(--bg-card);
  border-radius: 24rpx;
  padding: 48rpx;
  text-align: center;
  box-shadow: var(--shadow-card);
  margin-bottom: 32rpx;
}
.avatar-wrap {
  width: 160rpx; height: 160rpx;
  margin: 0 auto 24rpx;
  border-radius: 50%;
  background: var(--primary-bg);
  position: relative;
  overflow: hidden;
}
.avatar-img {
  position: absolute;
  left: 0; top: 0; right: 0; bottom: 0;
  width: 100% !important;
  height: 100% !important;
  display: block;
}
.avatar-placeholder { font-size: 80rpx; }
.nickname { font-size: 36rpx; font-weight: 600; color: var(--text); display: block; }
.desc { font-size: 26rpx; color: var(--text-hint); margin-top: 12rpx; display: block; }
.auth-row { margin-top: 24rpx; }
.btn-auth {
  width: 240rpx; height: 64rpx; line-height: 64rpx; font-size: 28rpx;
  border-radius: 32rpx; background: var(--primary); color: #fff; border: none;
}
.btn-auth::after { border: none; }
.btn-auth.secondary { background: transparent; color: var(--text-hint); border: 1rpx solid #ddd; }
.menu {
  background: var(--bg-card);
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: var(--shadow-card);
}
.menu-item { display: flex; align-items: center; padding: 32rpx 24rpx; border-bottom: 1rpx solid #f0f0f0; }
.menu-item:last-child { border-bottom: none; }
.menu-icon { font-size: 40rpx; margin-right: 24rpx; color: var(--primary); }
.menu-text { flex: 1; font-size: 30rpx; color: var(--text); }
.menu-arrow { font-size: 36rpx; color: var(--text-hint); }
.storage-card {
  margin-top: 32rpx;
  background: var(--bg-card);
  border-radius: 24rpx;
  padding: 28rpx 24rpx;
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}
.storage-header { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; }
.storage-label { font-size: 28rpx; color: var(--text-hint); }
.storage-progress-wrap { width: 100%; }
.storage-progress-track {
  height: 16rpx;
  background: #eee;
  border-radius: 8rpx;
  overflow: hidden;
}
.storage-progress-fill {
  height: 100%;
  border-radius: 8rpx;
  background: var(--primary);
  transition: width 0.2s ease;
}
.storage-value { font-size: 26rpx; color: var(--text); }
.storage-debug { font-size: 22rpx; color: var(--text-hint); margin-top: 8rpx; }
.btn-clear-cache { flex-shrink: 0; }
.tabbar-placeholder { height: 120rpx; }
</style>
