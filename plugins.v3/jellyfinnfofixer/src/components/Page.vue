<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'JellyfinNfoFixer' },
})

const emit = defineEmits(['close'])
const loading = ref(false)
const running = ref(false)
const message = reactive({ text: '', type: 'info' })
const status = reactive({ enabled: false, movie_library_dirs: [] })

function showMessage(text, type = 'info') {
  message.text = text
  message.type = type
  if (text) setTimeout(() => { if (message.text === text) message.text = '' }, 4000)
}

async function loadStatus() {
  loading.value = true
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'JellyfinNfoFixer'}/status`)
    const result = response?.data ?? response
    if (result?.success !== false) {
      Object.assign(status, result?.data ?? result ?? {})
    }
  } catch (error) {
    /* 忽略状态读取失败 */
  } finally {
    loading.value = false
  }
}

async function fixAll() {
  running.value = true
  try {
    const response = await props.api.post(`plugin/${props.pluginId || 'JellyfinNfoFixer'}/fix_nfo`, {})
    const result = response?.data ?? response
    if (result?.success === false) throw new Error(result.message || '执行失败')
    showMessage(result?.message || '已完成', 'success')
  } catch (error) {
    showMessage(error?.message || '执行失败', 'error')
  } finally {
    running.value = false
  }
}

onMounted(loadStatus)
</script>

<template>
  <div class="pa-4">
    <VToolbar density="comfortable" color="transparent" class="px-0">
      <VIcon icon="mdi-file-document-check-outline" color="primary" class="me-2" />
      <div class="text-h6">Jellyfin Nfo命名修复</div>
      <VSpacer />
      <VBtn icon="mdi-refresh" variant="text" :loading="loading" title="刷新状态" @click="loadStatus" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider class="mb-4" />
    <VAlert v-if="message.text" :type="message.type" variant="tonal" density="compact" class="mb-4">{{ message.text }}</VAlert>

    <VAlert v-if="!status.enabled" type="warning" variant="tonal" density="compact" class="mb-4">
      插件未启用，请在「配置」中启用。
    </VAlert>
    <template v-else>
      <VCard variant="outlined">
        <VCardText>
          <div class="text-subtitle-2 mb-1">电影库目录</div>
          <div class="text-body-2">{{ (status.movie_library_dirs || []).join('、') || '未配置' }}</div>
        </VCardText>
      </VCard>
      <div class="d-flex justify-end mt-4">
        <VBtn color="primary" prepend-icon="mdi-play" :loading="running" @click="fixAll">立即全库补齐 movie.nfo</VBtn>
      </div>
    </template>
  </div>
</template>

