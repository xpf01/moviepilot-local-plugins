<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'TpdbScraper' },
})

const emit = defineEmits(['close'])
const running = ref(false)
const message = reactive({ text: '', type: 'info' })
const status = reactive({ enabled: false, has_token: false, library_dirs: [], last_result: null })

function showMessage(text, type = 'info') {
  message.text = text
  message.type = type
  if (text) setTimeout(() => { if (message.text === text) message.text = '' }, 4000)
}

async function loadStatus() {
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'TpdbScraper'}/status`)
    const result = response?.data ?? response
    if (result?.success !== false) {
      Object.assign(status, result?.data ?? result ?? {})
    }
  } catch (error) {
    /* 忽略状态读取失败 */
  }
}

async function scrapeNow() {
  running.value = true
  try {
    const response = await props.api.post(`plugin/${props.pluginId || 'TpdbScraper'}/scrape_now`, {})
    const result = response?.data ?? response
    if (result?.success === false) throw new Error(result.message || '刮削失败')
    const data = result?.data ?? {}
    showMessage(`刮削完成：共 ${data.total ?? 0}，命中 ${data.matched ?? 0}，失败 ${data.failed ?? 0}`, 'success')
    await loadStatus()
  } catch (error) {
    showMessage(error?.message || '刮削失败', 'error')
  } finally {
    running.value = false
  }
}

onMounted(loadStatus)
</script>

<template>
  <div class="pa-4">
    <VToolbar density="comfortable" color="transparent" class="px-0">
      <VIcon icon="mdi-movie-search" color="primary" class="me-2" />
      <div class="text-h6">ThePornDB 成人刮削</div>
      <VSpacer />
      <VBtn icon="mdi-refresh" variant="text" title="刷新状态" @click="loadStatus" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider class="mb-4" />
    <VAlert v-if="message.text" :type="message.type" variant="tonal" density="compact" class="mb-4">{{ message.text }}</VAlert>

    <VAlert v-if="!status.enabled" type="warning" variant="tonal" density="compact" class="mb-4">
      插件未启用，请在「配置」中启用并填写 API Token。
    </VAlert>
    <template v-else>
      <VRow dense>
        <VCol cols="12" md="4">
          <VCard variant="outlined">
            <VCardText>
              <div class="text-caption text-medium-emphasis">启用状态</div>
              <div class="text-h6">{{ status.enabled ? '已启用' : '未启用' }}</div>
            </VCardText>
          </VCard>
        </VCol>
        <VCol cols="12" md="4">
          <VCard variant="outlined">
            <VCardText>
              <div class="text-caption text-medium-emphasis">API Token</div>
              <div class="text-h6">{{ status.has_token ? '已配置' : '未配置' }}</div>
            </VCardText>
          </VCard>
        </VCol>
        <VCol cols="12" md="4">
          <VCard variant="outlined">
            <VCardText>
              <div class="text-caption text-medium-emphasis">刮削目录</div>
              <div class="text-body-2">{{ (status.library_dirs || []).join(', ') || '未配置' }}</div>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>

      <VCard v-if="status.last_result" variant="outlined" class="mt-4">
        <VCardText>
          <div class="text-subtitle-2 mb-1">上次刮削结果（{{ status.last_result.finished_at }}）</div>
          <div class="text-body-2">
            共 {{ status.last_result.total ?? 0 }} 个条目，命中 {{ status.last_result.matched ?? 0 }}，
            失败 {{ status.last_result.failed ?? 0 }}
          </div>
        </VCardText>
      </VCard>
    </template>

    <div class="d-flex justify-end mt-4">
      <VBtn color="primary" prepend-icon="mdi-play" :loading="running" @click="scrapeNow">立即全库刮削</VBtn>
    </div>
  </div>
</template>
