<template>
  <image
    v-if="displaySrc"
    :src="displaySrc"
    :mode="mode"
    :class="imgClass"
    :style="imgStyle"
    @error="onError"
    @load="onLoad"
  />
</template>

<script setup>
import { ref, watch } from 'vue'
import { getCachedImageUrl } from '@/utils/image-cache.js'

const props = defineProps({
  /** 远程图片完整 URL 或 data URL */
  src: { type: String, default: '' },
  mode: { type: String, default: 'aspectFill' },
  imgClass: { type: String, default: '' },
  imgStyle: { type: [String, Object], default: '' },
  /** 为 true 时跳过缓存，始终用远程 URL（用于头像等需完整缩略显示的图，避免本地路径下显示异常） */
  skipCache: { type: Boolean, default: false }
})

const emit = defineEmits(['error', 'load'])

const displaySrc = ref('')

function loadSrc(url) {
  if (!url || url.startsWith('data:')) {
    displaySrc.value = url || ''
    return
  }
  if (props.skipCache) {
    displaySrc.value = url
    return
  }
  getCachedImageUrl(url).then((res) => {
    displaySrc.value = res || url
  }).catch(() => {
    displaySrc.value = url
  })
}

watch(() => props.src, (url) => {
  loadSrc(url)
}, { immediate: true })

function onError(e) {
  if (displaySrc.value && displaySrc.value !== props.src) {
    displaySrc.value = props.src
  }
  emit('error', e)
}

function onLoad(e) {
  emit('load', e)
}
</script>
