<template>
  <view class="page">
    <!-- 连续学习 -->
    <view class="card">
      <view class="card-head">
        <text class="card-icon">🔥</text>
        <text class="card-title">连续学习 {{ streak }} 天</text>
      </view>
      <text class="card-desc">继续保持! 坚持就是胜利 💪</text>
      <view class="activity-grid">
        <view class="grid-cell" v-for="(cell, i) in activityCells" :key="i" :class="cell"></view>
      </view>
      <view class="legend">
        <text>少</text>
        <view class="legend-cells">
          <view class="legend-cell l0"></view>
          <view class="legend-cell l1"></view>
          <view class="legend-cell l2"></view>
          <view class="legend-cell l3"></view>
        </view>
        <text>多</text>
      </view>
    </view>

    <!-- 薄弱学科分析 -->
    <view class="card">
      <view class="card-title">薄弱学科分析</view>
      <text class="card-desc">图形凸出的方向表示薄弱点</text>
      <view class="radar-wrap">
        <view class="radar-bg">
          <view class="radar-fill" :style="radarStyle"></view>
        </view>
        <view class="radar-labels">
          <text class="rlabel" v-for="(l, i) in radarLabels" :key="i">{{ l.name }}</text>
        </view>
      </view>
      <view class="tip" v-if="weakTip">
        <text class="tip-icon">⚠</text>
        <text class="tip-text">{{ weakTip }}</text>
      </view>
    </view>

    <!-- 未来复习预测 -->
    <view class="card">
      <view class="card-title">未来复习预测</view>
      <text class="card-desc">艾宾浩斯记忆曲线预测</text>
      <view class="predict-value">{{ predictCount }}</view>
      <text class="predict-unit">题</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getTodayReviews } from '@/api/reviews.js'
import { listSubjects } from '@/api/subjects.js'

const streak = ref(1)
const activityCells = ref([])
const radarLabels = ref([{ name: '数学' }, { name: '语文' }, { name: '英语' }, { name: '物理' }, { name: '化学' }])
const radarData = ref([0.8, 0.5, 0.6, 0.5, 0.5])
const weakTip = ref('')
const predictCount = ref(0)

const radarStyle = computed(() => {
  const per = radarData.value.map((v, i) => (i * 20 + 50) + '%')
  return { width: '80%', height: '80%', margin: '10%', background: 'linear-gradient(135deg, rgba(74,144,226,0.35) 0%, rgba(74,144,226,0.15) 100%)', borderRadius: '50%' }
})

onMounted(async () => {
  const cols = 7
  const rows = 5
  const total = cols * rows
  const arr = []
  for (let i = 0; i < total; i++) {
    if (i === total - 2) arr.push('active')
    else arr.push('')
  }
  activityCells.value = arr

  try {
    const reviews = await getTodayReviews()
    predictCount.value = reviews.length
    if (reviews.length > 0) {
      const subjectCount = {}
      reviews.forEach(q => {
        subjectCount[q.subject_id] = (subjectCount[q.subject_id] || 0) + 1
      })
      const subjIds = Object.keys(subjectCount)
      if (subjIds.length) {
        const subjects = await listSubjects()
        const maxId = parseInt(subjIds.sort((a, b) => subjectCount[b] - subjectCount[a])[0], 10)
        const name = (subjects.find(s => s.id === maxId) || {}).name || '该科目'
        weakTip.value = `${name}有${subjectCount[maxId]}道题未掌握`
      }
    }
  } catch (e) {}
})
</script>

<style scoped>
.page { padding: 32rpx; background: var(--bg-page); min-height: 100vh; }
.card { background: var(--bg-card); border-radius: 24rpx; padding: 32rpx; margin-bottom: 32rpx; box-shadow: var(--shadow-card); }
.card-head { display: flex; align-items: center; gap: 12rpx; }
.card-icon { font-size: 36rpx; color: var(--primary); }
.card-title { font-size: 32rpx; font-weight: 600; color: var(--text); }
.card-desc { display: block; font-size: 26rpx; color: var(--text-secondary); margin-top: 12rpx; }
.activity-grid { display: flex; flex-wrap: wrap; gap: 8rpx; margin-top: 24rpx; }
.grid-cell { width: 32rpx; height: 32rpx; background: var(--bg-page); border-radius: 6rpx; }
.grid-cell.active { background: var(--primary-light); }
.legend { display: flex; align-items: center; gap: 16rpx; margin-top: 20rpx; font-size: 24rpx; color: var(--text-hint); }
.legend-cells { display: flex; gap: 8rpx; }
.legend-cell { width: 24rpx; height: 24rpx; border-radius: 4rpx; }
.legend-cell.l0 { background: var(--bg-page); }
.legend-cell.l1 { background: var(--primary-bg); }
.legend-cell.l2 { background: var(--primary-light); }
.legend-cell.l3 { background: var(--primary); }
.radar-wrap { position: relative; height: 280rpx; margin: 24rpx 0; }
.radar-bg { width: 240rpx; height: 240rpx; margin: 0 auto; border-radius: 50%; background: var(--primary-bg); display: flex; align-items: center; justify-content: center; }
.radar-fill { border-radius: 50%; }
.radar-labels { display: flex; justify-content: space-between; margin-top: 16rpx; padding: 0 24rpx; font-size: 24rpx; color: var(--text-secondary); }
.tip { display: flex; align-items: center; gap: 12rpx; padding: 20rpx; background: #fffbe6; border-radius: 12rpx; margin-top: 16rpx; }
.tip-icon { font-size: 32rpx; color: var(--warn); }
.tip-text { font-size: 26rpx; color: var(--text-secondary); }
.predict-value { font-size: 72rpx; font-weight: 600; color: var(--primary); text-align: center; margin-top: 24rpx; }
.predict-unit { display: block; text-align: center; font-size: 28rpx; color: var(--text-hint); margin-top: 8rpx; }
</style>
