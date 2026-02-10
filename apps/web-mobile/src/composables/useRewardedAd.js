/**
 * 激励视频广告：创建实例并在观看完成后请求后端加积分。
 * 用于「我的」页、错题本列表/报告页积分不足时直接拉广告。
 */
import { onMounted } from 'vue'
import request from '@/api/request.js'
import { AD_REWARD_UNIT_ID } from '@/config.js'

const POINTS_PER_AD = 10
let rewardedVideoAd = null

export function useRewardedAd() {
  onMounted(() => {
    if (!AD_REWARD_UNIT_ID) return
    try {
      rewardedVideoAd = uni.createRewardedVideoAd({ adUnitId: AD_REWARD_UNIT_ID })
      rewardedVideoAd.onClose((res) => {
        if (res && res.isEnded) {
          request.post('/auth/points/ad-reward').then(() => {
            uni.showToast({ title: `+${POINTS_PER_AD} 积分`, icon: 'success' })
          }).catch((e) => {
            uni.showToast({ title: e.message || '领取失败', icon: 'none' })
          })
        }
      })
      rewardedVideoAd.onError(() => {
        uni.showToast({ title: '广告加载失败', icon: 'none' })
      })
    } catch (e) {
      console.warn('createRewardedVideoAd not available', e)
    }
  })

  function showAd() {
    if (!AD_REWARD_UNIT_ID) {
      uni.showToast({ title: '暂未配置广告位', icon: 'none' })
      return
    }
    if (!rewardedVideoAd) {
      uni.showToast({ title: '广告未就绪', icon: 'none' })
      return
    }
    rewardedVideoAd.show().catch(() => {
      rewardedVideoAd.load().then(() => rewardedVideoAd.show()).catch(() => {
        uni.showToast({ title: '广告加载失败，请稍后再试', icon: 'none' })
      })
    })
  }

  return { showAd }
}
