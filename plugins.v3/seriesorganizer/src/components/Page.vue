<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'SeriesOrganizer' },
})

const emit = defineEmits(['close'])
const loading = ref(false)
const message = reactive({ text: '', type: 'info' })
const status = reactive({ enabled: false, notify: true, dry_run: false, series_count: 0, series_map: {} })

function showMessage(text, type = 'info') {
  message.text = text
  message.type = type
  if (text) setTimeout(() => { if (message.text === text) message.text = '' }, 4000)
}

async function loadStatus() {
  loading.value = true
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'SeriesOrganizer'}/status`)
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

onMounted(loadStatus)
</script>

<template>
  <div class="pa-4">
    <VToolbar density="comfortable" color="transparent" class="px-0">
      <VIcon icon="mdi-folder-multiple" color="primary" class="me-2" />
      <div class="text-h6">系列自动归组</div>
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
      <VRow dense>
        <VCol cols="12" md="4">
          <VCard variant="outlined">
            <VCardText>
              <div class="text-caption text-medium-emphasis">启用状态</div>
              <div class="text-h6">已启用</div>
            </VCardText>
          </VCard>
        </VCol>
        <VCol cols="12" md="4">
          <VCard variant="outlined">
            <VCardText>
              <div class="text-caption text-medium-emphasis">通知提示</div>
              <div class="text-h6">{{ status.notify ? '开启' : '关闭' }}</div>
            </VCardText>
          </VCard>
        </VCol>
        <VCol cols="12" md="4">
          <VCard variant="outlined">
            <VCardText>
              <div class="text-caption text-medium-emphasis">演练模式</div>
              <div class="text-h6">{{ status.dry_run ? '开启' : '关闭' }}</div>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>

      <VCard variant="outlined" class="mt-4">
        <VCardText>
          <div class="text-subtitle-2 mb-1">系列映射表（{{ status.series_count }} 个系列）</div>
          <div class="text-body-2">{{ Object.keys(status.series_map || {}).join('、') || '未配置' }}</div>
        </VCardText>
      </VCard>
    </template>
  </div>
</template>

