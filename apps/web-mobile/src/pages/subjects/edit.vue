<template>
  <view class="page">
    <view class="form">
      <view class="row">
        <text class="label">科目</text>
        <picker :range="courseOptions" range-key="label" :value="courseIndex" @change="onCourseChange">
          <view class="picker-value">{{ courseOptions[courseIndex]?.label || '请选择科目' }}</view>
        </picker>
      </view>
      <view class="row" v-if="isCustomCourse">
        <text class="label">自定义科目名</text>
        <input class="input" v-model="customCourseName" placeholder="请输入科目名称" />
      </view>
      <view class="row">
        <text class="label">错题本名称</text>
        <input class="input" v-model="form.name" placeholder="请输入错题本名称" />
      </view>
      <view class="row">
        <text class="label">排序</text>
        <input class="input" type="number" v-model.number="form.sort" placeholder="0" />
      </view>
      <button class="btn primary" @click="submit">保存</button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { createSubject, updateSubject, getSubject } from '@/api/subjects.js'
import { COURSE_PICKER_OPTIONS, CUSTOM_COURSE_LABEL } from '@/utils/course.js'

const id = ref(null)
const form = ref({ name: '', sort: 0, course: '' })
const courseIndex = ref(0)
const customCourseName = ref('')

const courseOptions = ref(COURSE_PICKER_OPTIONS.map((c) => ({ label: c, value: c })))
const isCustomCourse = computed(() => courseOptions.value[courseIndex.value]?.value === CUSTOM_COURSE_LABEL)

function getEffectiveCourse() {
  if (isCustomCourse.value && customCourseName.value.trim()) return customCourseName.value.trim()
  const v = courseOptions.value[courseIndex.value]?.value
  return v === CUSTOM_COURSE_LABEL ? '' : (v || '')
}

function onCourseChange(e) {
  courseIndex.value = Number(e.detail.value)
}

function applyCourse(course) {
  if (course == null || course === '') return
  const i = COURSE_PICKER_OPTIONS.indexOf(course)
  if (i >= 0) courseIndex.value = i
  else {
    courseIndex.value = COURSE_PICKER_OPTIONS.length - 1
    customCourseName.value = course
  }
  form.value.course = course
}

function applyOptions(opts) {
  if (!opts) return
  if (opts.id) {
    id.value = parseInt(opts.id, 10)
    form.value.name = opts.name ? decodeURIComponent(opts.name) : ''
    form.value.sort = parseInt(opts.sort, 10) || 0
    if (opts.course != null) applyCourse(decodeURIComponent(opts.course))
    uni.setNavigationBarTitle({ title: form.value.name || '编辑' })
  } else {
    uni.setNavigationBarTitle({ title: '新建错题本' })
  }
}

onLoad((opts) => {
  applyOptions(opts)
})

onMounted(async () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1]
  const opts = page.options || {}
  applyOptions(opts)
  if (opts.id) {
    try {
      const s = await getSubject(parseInt(opts.id, 10))
      if (s) {
        form.value.name = s.name || form.value.name
        form.value.sort = s.sort ?? form.value.sort
        if (s.course != null) applyCourse(s.course)
      }
    } catch (_) {}
  }
})

async function submit() {
  if (!form.value.name.trim()) {
    uni.showToast({ title: '请输入错题本名称', icon: 'none' })
    return
  }
  if (isCustomCourse.value && !customCourseName.value.trim()) {
    uni.showToast({ title: '请输入自定义科目名', icon: 'none' })
    return
  }
  const course = getEffectiveCourse()
  try {
    if (id.value) {
      await updateSubject(id.value, { name: form.value.name.trim(), course: course || null, sort: form.value.sort })
      uni.showToast({ title: '已更新' })
    } else {
      await createSubject({ name: form.value.name.trim(), course: course || null, sort: form.value.sort })
      uni.showToast({ title: '已添加' })
    }
    setTimeout(() => uni.navigateBack(), 500)
  } catch (e) {
    uni.showToast({ title: e.message || '保存失败', icon: 'none' })
  }
}
</script>

<style scoped>
.page { background: var(--bg-page); min-height: 100vh; padding: 32rpx; }
.form { background: var(--bg-card); border-radius: 24rpx; padding: 32rpx; box-shadow: var(--shadow-card); }
.row { margin-bottom: 32rpx; }
.label { display: block; font-size: 28rpx; color: var(--text-secondary); margin-bottom: 12rpx; }
.picker-value { padding: 24rpx; border: 1rpx solid #eee; border-radius: 12rpx; font-size: 30rpx; color: var(--text); }
.input { padding: 24rpx; border: 1rpx solid #eee; border-radius: 12rpx; font-size: 30rpx; color: var(--text); }
.btn { margin-top: 24rpx; padding: 28rpx; border-radius: 24rpx; font-size: 30rpx; }
.primary { background: var(--primary); color: #fff; border: none; }
</style>
