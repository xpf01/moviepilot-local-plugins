<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'MediaExplore' },
})

const emit = defineEmits(['close'])
const loading = ref(false)
const status = reactive({ enabled: false, sources: {} })

const LABELS = {
  tencentvideo: '腾讯视频',
  bilibili: '哔哩哔哩',
  cctv: 'CCTV',
  mangguo: '芒果TV',
  bangumidaily: 'Bangumi每日放送',
  migu: '咪咕视频',
  iqiyi: '爱奇艺',
  maoyan: '猫眼TOP30',
}

async function loadStatus() {
  loading.value = true
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'MediaExplore'}/status`)
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
      <VIcon icon="mdi-compass-outline" color="primary" class="me-2" />
      <div class="text-h6">媒体探索聚合</div>
      <VSpacer />
      <VBtn icon="mdi-refresh" variant="text" :loading="loading" title="刷新状态" @click="loadStatus" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider class="mb-4" />

    <VAlert v-if="!status.enabled" type="warning" variant="tonal" density="compact" class="mb-4">
      尚未开启任何探索源，请在「配置」中开启。
    </VAlert>
    <VCard variant="outlined">
      <VCardText>
        <div class="text-subtitle-2 mb-2">探索源状态</div>
        <VRow dense>
          <VCol v-for="(label, key) in LABELS" :key="key" cols="6" md="4">
            <div class="d-flex align-center py-1">
              <VIcon :icon="status.sources?.[key] ? 'mdi-check-circle' : 'mdi-circle-outline'" :color="status.sources?.[key] ? 'success' : undefined" class="me-2" size="small" />
              <span class="text-body-2">{{ label }}</span>
            </div>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>
  </div>
</template>

