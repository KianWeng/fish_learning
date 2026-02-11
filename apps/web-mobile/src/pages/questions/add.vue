<template>
  <view class="page">
    <view class="section empty-section" v-if="!result">
      <text class="empty-tip">请从错题本或章节页点击 + 拍照添加错题</text>
      <button class="btn default" @click="goBack">返回</button>
    </view>
    <view class="section" v-else>
      <view class="preview" v-if="previewImageUrl">
        <image :src="previewImageUrl" mode="widthFix" class="img" />
      </view>
      <view class="field">
        <text class="label">题目</text>
        <textarea class="textarea" v-model="form.content" placeholder="题目内容" :maxlength="-1" />
      </view>
      <view class="field summary-field" v-if="form.summary">
        <text class="label">知识点·易错点</text>
        <scroll-view class="summary-wrap" scroll-y>{{ form.summary }}</scroll-view>
      </view>
      <view class="field">
        <text class="label">解析</text>
        <textarea class="textarea textarea-analysis" v-model="form.analysis" placeholder="解析" :maxlength="-1" />
      </view>
      <view class="field">
        <text class="label">答案</text>
        <textarea class="textarea textarea-answer" v-model="form.answer" placeholder="答案" :maxlength="-1" />
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
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TabBar from '@/components/TabBar.vue'
import { API_BASE_URL } from '@/config.js'
import { listSubjects, createSubject } from '@/api/subjects.js'
import { listChapters } from '@/api/chapters.js'
import { uploadAndAnalyzeImage, createQuestion, deleteQuestionImage } from '@/api/questions.js'
import { setSourcePath, getResultPath, clear } from '@/utils/crop-store.js'

const result = ref(null)
const form = ref({ content: '', analysis: '', answer: '', image_url: '', summary: '', subject_id: 0, chapter_id: null })
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
/** 本地裁剪图路径（识别界面上展示用户裁剪的那张图） */
const croppedImagePath = ref('')
watch(() => result.value?.url, (url) => {
  if (url) imageFullUrl.value = url.startsWith('http') ? url : API_BASE_URL + url
}, { immediate: true })
const previewImageUrl = computed(() => croppedImagePath.value || imageFullUrl.value)

async function loadSubjects() {
  try {
    subjects.value = await listSubjects()
  } catch (e) {
    uni.showToast({ title: e.message || '加载科目失败', icon: 'none' })
  }
}

watch(subjectId, async (id) => {
  if (!id) { chapters.value = []; chapterId.value = null; chapterName.value = ''; return }
  try {
    chapters.value = await listChapters(id)
    if (pendingChapterId.value) {
      const c = chapters.value.find(x => x.id === pendingChapterId.value)
      if (c) {
        chapterId.value = c.id
        chapterName.value = c.name
      }
      pendingChapterId.value = null
      pendingChapterName.value = ''
    }
  } catch (e) {
    chapters.value = []
  }
})

const pendingChapterId = ref(null)
const pendingChapterName = ref('')

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
  openCameraOrAlbum(['album', 'camera'])
}

/** 仅拍照，用于 openCamera=1 时直接打开相机 */
function openCameraOnly() {
  openCameraOrAlbum(['camera'])
}

function openCameraOrAlbum(sourceType) {
  uni.chooseImage({
    count: 1,
    sourceType,
    success: (res) => {
      const path = res.tempFilePaths[0]
      setSourcePath(path)
      uni.navigateTo({ url: '/pages/common/image-crop' })
    }
  })
}

/** 后端返回的 content 是否为识别失败（未配置、分析失败、超时等） */
function isRecognitionFailure(data) {
  if (!data || !data.url) {
    console.log('[add] isRecognitionFailure false: 无 data 或 data.url', { hasData: !!data, hasUrl: !!data?.url })
    return false
  }
  const content = (data.content && typeof data.content === 'string') ? data.content.trim() : ''
  if (!content) {
    console.log('[add] isRecognitionFailure false: content 为空')
    return false
  }
  const keywords = ['[', '未配置', '请配置', '请设置', '分析失败', '请求失败', '识别失败', '超时', '请稍后重试', '换一张']
  const matched = keywords.some(k => (k === '[' ? content.startsWith('[') : content.includes(k)))
  console.log('[add] isRecognitionFailure check content=', content.slice(0, 80), 'matched=', matched)
  return matched
}

async function useCroppedImage(croppedPath) {
  if (!croppedPath) return
  croppedImagePath.value = croppedPath
  uni.showLoading({ title: '识别中...' })
  try {
    const data = await uploadAndAnalyzeImage(croppedPath)
    console.log('[add] uploadAndAnalyzeImage 返回 data=', { url: data?.url, contentLen: data?.content?.length, contentPreview: data?.content?.slice?.(0, 80) })
    uni.hideLoading()
    clear()
    const isFail = isRecognitionFailure(data)
    console.log('[add] isRecognitionFailure=', isFail, 'hasUrl=', !!data?.url, 'contentPreview=', data?.content?.slice?.(0, 60))
    if (isFail) {
      console.log('[add] 进入识别失败弹窗分支')
      uni.showModal({
        title: '识别失败',
        content: '是否手动输入错题？选择「手动输入」可保留图片并自行填写；选择「取消」将删除本次上传的图片。',
        confirmText: '手动输入',
        cancelText: '取消',
        success: async (res) => {
          if (res.confirm) {
            result.value = { url: data.url, content: '', analysis: '', answer: '', summary: data.summary || '' }
            form.value.content = ''
            form.value.analysis = ''
            form.value.answer = ''
            form.value.image_url = data.url || ''
            form.value.summary = data.summary || ''
            imageFullUrl.value = (data.url && !data.url.startsWith('http')) ? (API_BASE_URL.replace(/\/$/, '') + (data.url.startsWith('/') ? data.url : '/' + data.url)) : (data.url || '')
            await nextTick()
          } else {
            if (data.url) {
              try {
                await deleteQuestionImage(data.url)
              } catch (_) {}
            }
            reset()
            goBack()
          }
        }
      })
      return
    }
    console.log('[add] 识别成功，填充表单')
    result.value = data
    form.value.content = data.content || ''
    form.value.analysis = data.analysis || ''
    form.value.answer = data.answer || ''
    form.value.image_url = data.url || ''
    form.value.summary = data.summary || ''
  } catch (e) {
    console.warn('[add] useCroppedImage catch', e?.message || e?.errMsg || e, 'name=', e?.name)
    uni.hideLoading()
    const msg = e?.errMsg || e?.message || ''
    const isTimeout = typeof msg === 'string' && msg.includes('timeout')
    uni.showToast({
      title: isTimeout ? '请求超时，识图较慢请稍后重试或换一张' : (msg || '上传或识别失败'),
      icon: 'none'
    })
    clear()
  }
}

function reset() {
  result.value = null
  croppedImagePath.value = ''
  form.value = { content: '', analysis: '', answer: '', image_url: '', summary: '', subject_id: 0, chapter_id: null }
  subjectId.value = 0
  subjectName.value = ''
  chapterId.value = null
  chapterName.value = ''
  if (createBookMode.value) bookName.value = ''
}

function goBack() {
  uni.navigateBack()
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
      summary: form.value.summary || undefined,
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

onShow(() => {
  const croppedPath = getResultPath()
  if (croppedPath) useCroppedImage(croppedPath)
})

onMounted(async () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1]
  const opts = page.options || {}
  createBookMode.value = opts.mode === 'createBook'
  await loadSubjects()
  const sid = opts.subject_id ? parseInt(opts.subject_id, 10) : 0
  const cid = opts.chapter_id ? parseInt(opts.chapter_id, 10) : null
  if (sid && !createBookMode.value) {
    if (cid) {
      pendingChapterId.value = cid
      pendingChapterName.value = opts.chapter_name ? decodeURIComponent(opts.chapter_name) : ''
    }
    const s = subjects.value.find(x => x.id === sid)
    if (s) {
      subjectId.value = s.id
      subjectName.value = s.name
    }
  }
})
</script>

<style scoped>
.page { padding: 24rpx 24rpx 140rpx; min-height: 100vh; background: #f5f6fa; }
.tabbar-placeholder { height: 120rpx; }
.section { background: #fff; border-radius: 12rpx; padding: 32rpx; margin-bottom: 24rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06); }
.btn { margin-top: 24rpx; padding: 28rpx; border-radius: 12rpx; font-size: 30rpx; width: 100%; }
.primary { background: #07c160; color: #fff; border: none; }
.default { background: #f0f0f0; color: #333; border: none; }
.tip { font-size: 24rpx; color: #999; margin-top: 16rpx; }
.empty-section { text-align: center; padding: 48rpx 32rpx; }
.empty-tip { display: block; font-size: 28rpx; color: #999; margin-bottom: 32rpx; }
.preview { margin-bottom: 24rpx; }
.img { width: 100%; border-radius: 8rpx; }
.field { margin-bottom: 24rpx; }
.label { display: block; font-size: 28rpx; color: #666; margin-bottom: 8rpx; }
.textarea {
  width: 100%;
  min-height: 200rpx;
  padding: 20rpx;
  border: 1rpx solid #eee;
  border-radius: 8rpx;
  font-size: 28rpx;
  line-height: 1.5;
  box-sizing: border-box;
}
.textarea-answer { min-height: 100rpx; }
.textarea-analysis { min-height: 280rpx; }
.input { width: 100%; min-height: 88rpx; padding: 24rpx; border: 1rpx solid #eee; border-radius: 8rpx; font-size: 30rpx; line-height: 1.5; box-sizing: border-box; }
.picker { padding: 24rpx; border: 1rpx solid #eee; border-radius: 8rpx; font-size: 30rpx; }
.summary-field { background: linear-gradient(135deg, #e8f5e9 0%, #fff8e1 100%); border-radius: 12rpx; padding: 24rpx; border: 1rpx solid #c8e6c9; }
.summary-wrap { height: 320rpx; font-size: 28rpx; color: #2e7d32; line-height: 1.5; white-space: pre-wrap; word-break: break-all; }
</style>
