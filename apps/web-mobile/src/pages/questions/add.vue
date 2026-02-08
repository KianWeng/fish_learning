<template>
  <view class="page">
    <view class="section" v-if="!result">
      <button class="btn primary" @click="chooseImage">选择照片 / 拍照</button>
      <view class="tip">将自动识别题目并生成解析与答案</view>
    </view>
    <view class="section" v-else>
      <view class="preview" v-if="result.url">
        <image :src="imageFullUrl" mode="widthFix" class="img" />
      </view>
      <view class="field">
        <text class="label">题目</text>
        <textarea class="textarea" v-model="form.content" placeholder="题目内容" />
      </view>
      <view class="field">
        <text class="label">解析</text>
        <textarea class="textarea" v-model="form.analysis" placeholder="解析" />
      </view>
      <view class="field">
        <text class="label">答案</text>
        <input class="input" v-model="form.answer" placeholder="答案" />
      </view>
      <view class="field" v-if="createBookMode">
        <text class="label">错题本名称</text>
        <input class="input" v-model="bookName" placeholder="输入错题本名字，不存在将自动创建" />
      </view>
      <view class="field" v-else>
        <text class="label">科目</text>
        <picker :range="subjects" range-key="name" @change="onSubjectChange">
          <view class="picker">{{ subjectName || '请选择科目' }}</view>
        </picker>
      </view>
      <view class="field" v-if="subjectId && !createBookMode">
        <text class="label">章节</text>
        <picker :range="chapters" range-key="name" @change="onChapterChange">
          <view class="picker">{{ chapterName || '可选章节' }}</view>
        </picker>
      </view>
      <button class="btn primary" @click="submit" :disabled="saving">保存错题</button>
      <button class="btn default" @click="reset">换一张</button>
    </view>
    <view class="tabbar-placeholder" />
    <TabBar current="" />
  </view>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import TabBar from '@/components/TabBar.vue'
import { API_BASE_URL } from '@/config.js'
import { listSubjects, createSubject } from '@/api/subjects.js'
import { listChapters } from '@/api/chapters.js'
import { uploadAndAnalyzeImage, createQuestion } from '@/api/questions.js'

const result = ref(null)
const form = ref({ content: '', analysis: '', answer: '', image_url: '', subject_id: 0, chapter_id: null })
const subjectId = ref(0)
const subjectName = ref('')
const chapterId = ref(null)
const chapterName = ref('')
const subjects = ref([])
const chapters = ref([])
const saving = ref(false)
/** 拍照创建模式：拍照后输入错题本名字，不存在则新建 */
const createBookMode = ref(false)
const bookName = ref('')

const imageFullUrl = ref('')
watch(() => result.value?.url, (url) => {
  if (url) imageFullUrl.value = url.startsWith('http') ? url : API_BASE_URL + url
}, { immediate: true })

async function loadSubjects() {
  try {
    subjects.value = await listSubjects()
  } catch (e) {
    uni.showToast({ title: e.message || '加载科目失败', icon: 'none' })
  }
}

watch(subjectId, async (id) => {
  if (!id) { chapters.value = []; return }
  try {
    chapters.value = await listChapters(id)
  } catch (e) {
    chapters.value = []
  }
})

function onSubjectChange(e) {
  const i = e.detail.value
  if (subjects.value[i]) {
    subjectId.value = subjects.value[i].id
    subjectName.value = subjects.value[i].name
    chapterId.value = null
    chapterName.value = ''
  }
}

function onChapterChange(e) {
  const i = e.detail.value
  if (chapters.value[i]) {
    chapterId.value = chapters.value[i].id
    chapterName.value = chapters.value[i].name
  }
}

function chooseImage() {
  uni.chooseImage({
    count: 1,
    sourceType: ['album', 'camera'],
    success: async (res) => {
      const path = res.tempFilePaths[0]
      uni.showLoading({ title: '识别中...' })
      try {
        const data = await uploadAndAnalyzeImage(path)
        uni.hideLoading()
        result.value = data
        form.value.content = data.content || ''
        form.value.analysis = data.analysis || ''
        form.value.answer = data.answer || ''
        form.value.image_url = data.url || ''
      } catch (e) {
        uni.hideLoading()
        uni.showToast({ title: e.message || '上传或识别失败', icon: 'none' })
      }
    }
  })
}

function reset() {
  result.value = null
  form.value = { content: '', analysis: '', answer: '', image_url: '', subject_id: 0, chapter_id: null }
  subjectId.value = 0
  subjectName.value = ''
  chapterId.value = null
  chapterName.value = ''
  if (createBookMode.value) bookName.value = ''
}

async function submit() {
  if (!form.value.content.trim()) {
    uni.showToast({ title: '请填写题目内容', icon: 'none' })
    return
  }
  let sid = subjectId.value
  if (createBookMode.value) {
    const name = bookName.value.trim()
    if (!name) {
      uni.showToast({ title: '请输入错题本名称', icon: 'none' })
      return
    }
    const exist = subjects.value.find(s => s.name === name)
    if (exist) {
      sid = exist.id
    } else {
      try {
        const sub = await createSubject({ name, sort: 0 })
        sid = sub.id
        subjects.value.push(sub)
      } catch (e) {
        uni.showToast({ title: e.message || '创建错题本失败', icon: 'none' })
        return
      }
    }
  }
  if (!sid) {
    uni.showToast({ title: '请选择科目', icon: 'none' })
    return
  }
  saving.value = true
  try {
    await createQuestion({
      subject_id: sid,
      chapter_id: createBookMode.value ? undefined : (chapterId.value || undefined),
      content: form.value.content.trim(),
      analysis: form.value.analysis || undefined,
      answer: form.value.answer || undefined,
      image_url: form.value.image_url || undefined,
      source: 'photo'
    })
    uni.showToast({ title: '已保存' })
    setTimeout(() => uni.navigateBack(), 500)
  } catch (e) {
    uni.showToast({ title: e.message || '保存失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1]
  const opts = page.options || {}
  createBookMode.value = opts.mode === 'createBook'
})

loadSubjects()
</script>

<style scoped>
.page { padding: 24rpx 24rpx 140rpx; min-height: 100vh; background: #f5f6fa; }
.tabbar-placeholder { height: 120rpx; }
.section { background: #fff; border-radius: 12rpx; padding: 32rpx; margin-bottom: 24rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06); }
.btn { margin-top: 24rpx; padding: 28rpx; border-radius: 12rpx; font-size: 30rpx; width: 100%; }
.primary { background: #07c160; color: #fff; border: none; }
.default { background: #f0f0f0; color: #333; border: none; }
.tip { font-size: 24rpx; color: #999; margin-top: 16rpx; }
.preview { margin-bottom: 24rpx; }
.img { width: 100%; border-radius: 8rpx; }
.field { margin-bottom: 24rpx; }
.label { display: block; font-size: 28rpx; color: #666; margin-bottom: 8rpx; }
.textarea { width: 100%; min-height: 160rpx; padding: 20rpx; border: 1rpx solid #eee; border-radius: 8rpx; font-size: 28rpx; box-sizing: border-box; }
.input { padding: 24rpx; border: 1rpx solid #eee; border-radius: 8rpx; font-size: 30rpx; width: 100%; box-sizing: border-box; }
.picker { padding: 24rpx; border: 1rpx solid #eee; border-radius: 8rpx; font-size: 30rpx; }
</style>
