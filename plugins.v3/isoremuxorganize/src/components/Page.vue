<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'IsoRemuxOrganize' },
})

const emit = defineEmits(['close'])
const loading = ref(false)
const status = reactive({
  enabled: false,
  scan_root: '',
  interval: 0,
  timeout: 0,
  notify: true,
  processed_count: 0,
})

async function loadStatus() {
  loading.value = true
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'IsoRemuxOrganize'}/status`)
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
      <VIcon icon="mdi-disc" color="primary" class="me-2" />
      <div class="text-h6">ISO原盘转封装</div>
      <VSpacer />
      <VBtn icon="mdi-refresh" variant="text" :loading="loading" title="刷新状态" @click="loadStatus" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider class="mb-4" />

    <VAlert v-if="!status.enabled" type="warning" variant="tonal" density="compact" class="mb-4">
      插件未启用，请在「配置」中启用。
    </VAlert>
    <template v-else>
      <VRow dense>
        <VCol cols="12" md="4">
          <VCard variant="outlined"><VCardText>
            <div class="text-caption text-medium-emphasis">扫描根目录</div>
            <div class="text-body-2">{{ status.scan_root || '未配置' }}</div>
          </VCardText></VCard>
        </VCol>
        <VCol cols="12" md="4">
          <VCard variant="outlined"><VCardText>
            <div class="text-caption text-medium-emphasis">扫描间隔（秒）</div>
            <div class="text-h6">{{ status.interval }}</div>
          </VCardText></VCard>
        </VCol>
        <VCol cols="12" md="4">
          <VCard variant="outlined"><VCardText>
            <div class="text-caption text-medium-emphasis">已处理 ISO 数</div>
            <div class="text-h6">{{ status.processed_count }}</div>
          </VCardText></VCard>
        </VCol>
      </VRow>
    </template>
  </div>
</template>

