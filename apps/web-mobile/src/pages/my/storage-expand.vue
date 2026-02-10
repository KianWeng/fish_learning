<template>
  <view class="page">
    <view class="card points-bar">
      <text class="points-label">当前积分</text>
      <text class="points-value">{{ points }}</text>
      <button class="btn-ad" :disabled="adLoading" @click="onWatchAd">观看广告 +{{ pointsPerAd }} 积分</button>
    </view>
    <view class="card tip">
      <text class="tip-text">使用积分兑换扩容包可增加云端容量，有效期为 1 年。</text>
    </view>
    <view class="packages">
      <view
        v-for="(pkg, i) in packages"
        :key="i"
        class="pkg-card"
        :class="{ selected: selectedIndex === i }"
        @click="selectedIndex = i"
      >
        <text class="pkg-size">+{{ pkg.label }}</text>
        <text class="pkg-desc">{{ pkg.desc }}</text>
        <text class="pkg-validity">有效期 1 年</text>
        <text class="pkg-price">{{ pkg.points }} 积分</text>
      </view>
    </view>
    <button class="btn primary" :disabled="loading || !canRedeem" @click="onRedeem">积分兑换</button>
    <view class="footer-hint">兑换成功后容量立即生效，1 年内有效</view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import request from '@/api/request.js'
import { AD_REWARD_UNIT_ID } from '@/config.js'

const pointsPerAd = 10
const packages = ref([
  { label: '50MB', add_bytes: 50 * 1024 * 1024, points: 500, desc: '约可存储 500+ 道题图片' },
  { label: '100MB', add_bytes: 100 * 1024 * 1024, points: 1000, desc: '约可存储 1000+ 道题图片' },
  { label: '200MB', add_bytes: 200 * 1024 * 1024, points: 2000, desc: '约可存储 2000+ 道题图片' }
])
const selectedIndex = ref(0)
const points = ref(0)
const loading = ref(false)
const adLoading = ref(false)
let rewardedVideoAd = null

const selectedPkg = computed(() => packages.value[selectedIndex.value])
const canRedeem = computed(() => selectedPkg.value && points.value >= selectedPkg.value.points)

onLoad(() => {
  uni.setNavigationBarTitle({ title: '存储扩容' })
})

onMounted(() => {
  fetchStorage()
  // #ifdef MP-WEIXIN
  if (AD_REWARD_UNIT_ID) {
    try {
      rewardedVideoAd = uni.createRewardedVideoAd({ adUnitId: AD_REWARD_UNIT_ID })
      rewardedVideoAd.onClose((res) => {
        if (res && res.isEnded) {
          request.post('/auth/points/ad-reward').then(() => {
            uni.showToast({ title: `+${pointsPerAd} 积分`, icon: 'success' })
            fetchStorage()
          }).catch((e) => {
            uni.showToast({ title: e.message || '领取失败', icon: 'none' })
          })
        }
      })
      rewardedVideoAd.onError((err) => {
        console.warn('激励视频广告错误', err)
        uni.showToast({ title: '广告加载失败', icon: 'none' })
      })
    } catch (e) {
      console.warn('createRewardedVideoAd not available', e)
    }
  }
  // #endif
})

async function fetchStorage() {
  try {
    const res = await request.get('/auth/storage')
    points.value = res.points ?? 0
  } catch (_) {}
}

function onWatchAd() {
  // #ifdef MP-WEIXIN
  if (!AD_REWARD_UNIT_ID) {
    uni.showToast({ title: '暂未配置广告位', icon: 'none' })
    return
  }
  if (!rewardedVideoAd) {
    uni.showToast({ title: '广告未就绪', icon: 'none' })
    return
  }
  adLoading.value = true
  rewardedVideoAd.show().catch((e) => {
    rewardedVideoAd.load().then(() => rewardedVideoAd.show()).catch(() => {
      uni.showToast({ title: '广告加载失败，请稍后再试', icon: 'none' })
    })
  }).finally(() => { adLoading.value = false })
  // #endif
  // #ifndef MP-WEIXIN
  uni.showToast({ title: '仅支持在微信小程序中观看', icon: 'none' })
  // #endif
}

async function onRedeem() {
  const pkg = selectedPkg.value
  if (!pkg || points.value < pkg.points) {
    uni.showToast({ title: '积分不足', icon: 'none' })
    return
  }
  loading.value = true
  try {
    await request.post('/auth/storage/redeem', { add_bytes: pkg.add_bytes })
    uni.showToast({ title: '兑换成功，有效期 1 年', icon: 'success' })
    await fetchStorage()
    setTimeout(() => uni.navigateBack(), 800)
  } catch (e) {
    uni.showToast({ title: e.message || '兑换失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page { padding: 32rpx; min-height: 100vh; background: var(--bg-page); }
.card { background: var(--bg-card); border-radius: 24rpx; padding: 28rpx; box-shadow: var(--shadow-card); }
.points-bar { margin-bottom: 24rpx; display: flex; align-items: center; flex-wrap: wrap; gap: 16rpx; }
.points-label { font-size: 28rpx; color: var(--text-secondary); }
.points-value { font-size: 40rpx; font-weight: 600; color: var(--primary); }
.btn-ad { margin-left: auto; padding: 16rpx 24rpx; font-size: 26rpx; background: var(--primary); color: #fff; border: none; border-radius: 16rpx; }
.tip { margin-bottom: 32rpx; }
.tip-text { font-size: 28rpx; color: var(--text-secondary); }
.packages { display: flex; flex-direction: column; gap: 20rpx; margin-bottom: 48rpx; }
.pkg-card {
  background: var(--bg-card);
  border-radius: 24rpx;
  padding: 32rpx;
  box-shadow: var(--shadow-card);
  border: 2rpx solid transparent;
}
.pkg-card.selected { border-color: var(--primary); background: var(--primary-bg); }
.pkg-size { display: block; font-size: 36rpx; font-weight: 600; color: var(--text); }
.pkg-desc { display: block; font-size: 24rpx; color: var(--text-hint); margin-top: 8rpx; }
.pkg-validity { display: block; font-size: 22rpx; color: var(--primary); margin-top: 6rpx; }
.pkg-price { display: block; font-size: 32rpx; color: var(--primary); font-weight: 600; margin-top: 12rpx; }
.btn { width: 100%; padding: 28rpx; border-radius: 24rpx; font-size: 30rpx; }
.primary { background: var(--primary); color: #fff; border: none; }
.footer-hint { text-align: center; font-size: 24rpx; color: var(--text-hint); margin-top: 24rpx; }
</style>
