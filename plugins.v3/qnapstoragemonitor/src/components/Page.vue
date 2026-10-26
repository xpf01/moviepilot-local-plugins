<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'QnapStorageMonitor' },
})

const emit = defineEmits(['close'])
const loading = ref(false)
const running = ref(false)
const message = reactive({ text: '', type: 'info' })
const status = reactive({ enabled: false, download_paused: false, last_report: '' })

function showMessage(text, type = 'info') {
  message.text = text
  message.type = type
  if (text) setTimeout(() => { if (message.text === text) message.text = '' }, 4000)
}

async function loadStatus() {
  loading.value = true
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'QnapStorageMonitor'}/status`)
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

async function checkNow() {
  running.value = true
  try {
    const response = await props.api.post(`plugin/${props.pluginId || 'QnapStorageMonitor'}/check_now`, {})
    const result = response?.data ?? response
    if (result?.success === false) throw new Error(result.message || '检查失败')
    await loadStatus()
    showMessage('检查完成', 'success')
  } catch (error) {
    showMessage(error?.message || '检查失败', 'error')
  } finally {
    running.value = false
  }
}

onMounted(loadStatus)
</script>

<template>
  <div class="pa-4">
    <VToolbar density="comfortable" color="transparent" class="px-0">
      <VIcon icon="mdi-database" color="primary" class="me-2" />
      <div class="text-h6">QNAP存储池监控</div>
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
      <VAlert :type="status.download_paused ? 'warning' : 'success'" variant="tonal" density="compact" class="mb-4">
        下载任务状态：{{ status.download_paused ? '已暂停（等待容量恢复）' : '正常' }}
      </VAlert>
      <VCard variant="outlined">
        <VCardText>
          <div class="text-subtitle-2 mb-1">最近检查结果</div>
          <div class="text-body-2">{{ status.last_report || '尚未执行检查' }}</div>
        </VCardText>
      </VCard>
      <div class="d-flex justify-end mt-4">
        <VBtn color="primary" prepend-icon="mdi-play" :loading="running" @click="checkNow">立即检查</VBtn>
      </div>
    </template>
  </div>
</template>

