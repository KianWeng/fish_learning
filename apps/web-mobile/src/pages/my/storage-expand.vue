<template>
  <view class="page">
    <view class="card tip">
      <text class="tip-text">当前存储空间不足时，可购买扩容包增加云端容量。</text>
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
        <text class="pkg-price">¥{{ pkg.price }}</text>
      </view>
    </view>
    <button class="btn primary" :disabled="loading" @click="onPurchase">立即购买</button>
    <view class="footer-hint">支付成功后容量将自动到账</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import request from '@/api/request.js'

const packages = ref([
  { label: '50MB', add_bytes: 50 * 1024 * 1024, price: '6', desc: '约可存储 500+ 道题图片' },
  { label: '100MB', add_bytes: 100 * 1024 * 1024, price: '10', desc: '约可存储 1000+ 道题图片' },
  { label: '200MB', add_bytes: 200 * 1024 * 1024, price: '18', desc: '约可存储 2000+ 道题图片' }
])
const selectedIndex = ref(0)
const loading = ref(false)

onLoad(() => {
  uni.setNavigationBarTitle({ title: '存储扩容' })
})

async function onPurchase() {
  const pkg = packages.value[selectedIndex.value]
  if (!pkg) return
  loading.value = true
  try {
    await request.post('/auth/storage/increase', { add_bytes: pkg.add_bytes })
    uni.showToast({ title: '扩容成功', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 800)
  } catch (e) {
    uni.showToast({ title: e.message || '购买失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

</script>

<style scoped>
.page { padding: 32rpx; min-height: 100vh; background: var(--bg-page); }
.card { background: var(--bg-card); border-radius: 24rpx; padding: 28rpx; box-shadow: var(--shadow-card); }
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
.pkg-price { display: block; font-size: 32rpx; color: var(--primary); font-weight: 600; margin-top: 16rpx; }
.btn { width: 100%; padding: 28rpx; border-radius: 24rpx; font-size: 30rpx; }
.primary { background: var(--primary); color: #fff; border: none; }
.footer-hint { text-align: center; font-size: 24rpx; color: var(--text-hint); margin-top: 24rpx; }
</style>
