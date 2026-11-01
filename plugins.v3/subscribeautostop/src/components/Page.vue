<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'SubscribeAutoStop' },
})

const emit = defineEmits(['close'])
const loading = ref(false)
const scanning = ref(false)
const message = reactive({ text: '', type: 'info' })
const status = reactive({ enabled: false, cron: '', action: 'pause', notify: false, last_report: null })

function showMessage(text, type = 'info') {
  message.text = text
  message.type = type
  if (text) setTimeout(() => { if (message.text === text) message.text = '' }, 4000)
}

async function loadStatus() {
  loading.value = true
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'SubscribeAutoStop'}/status`)
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

async function scanNow() {
  scanning.value = true
  try {
    const response = await props.api.post(`plugin/${props.pluginId || 'SubscribeAutoStop'}/scan`, {})
    const result = response?.data ?? response
    if (result?.success === false) {
      showMessage(result?.message || '扫描失败', 'error')
    } else {
      if (result?.data) status.last_report = result.data
      showMessage('扫描完成', 'success')
    }
  } catch (error) {
    showMessage(error?.message || '扫描失败', 'error')
  } finally {
    scanning.value = false
  }
}

onMounted(loadStatus)
</script>

<template>
  <div class="pa-4">
    <VToolbar density="comfortable" color="transparent" class="px-0">
      <VIcon icon="mdi-auto-download" color="primary" class="me-2" />
      <div class="text-h6">订阅入库自停</div>
      <VSpacer />
      <VBtn color="primary" :loading="scanning" @click="scanNow" class="me-2">
        <VIcon icon="mdi-play" class="me-1" />立即扫描
      </VBtn>
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
        <VCol cols="12" md="3">
          <VCard variant="outlined">
            <VCardText>
              <div class="text-caption text-medium-emphasis">定时表达式</div>
              <div class="text-h6">{{ status.cron }}</div>
            </VCardText>
          </VCard>
        </VCol>
        <VCol cols="12" md="3">
          <VCard variant="outlined">
            <VCardText>
              <div class="text-caption text-medium-emphasis">命中动作</div>
              <div class="text-h6">{{ status.action === 'delete' ? '删除订阅' : '暂停订阅' }}</div>
            </VCardText>
          </VCard>
        </VCol>
        <VCol cols="12" md="3">
          <VCard variant="outlined">
            <VCardText>
              <div class="text-caption text-medium-emphasis">通知</div>
              <div class="text-h6">{{ status.notify ? '开启' : '关闭' }}</div>
            </VCardText>
          </VCard>
        </VCol>
        <VCol cols="12" md="3">
          <VCard variant="outlined">
            <VCardText>
              <div class="text-caption text-medium-emphasis">最近命中</div>
              <div class="text-h6">{{ status.last_report ? status.last_report.hit_count : 0 }}</div>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>

      <VCard variant="outlined" class="mt-4">
        <VCardTitle class="text-subtitle-1">最近一次扫描报告</VCardTitle>
        <VCardText v-if="status.last_report">
          <div class="text-body-2 mb-2">
            共扫描 {{ status.last_report.scanned_count }} 条订阅，命中 {{ status.last_report.hit_count }} 条。
          </div>
          <div v-if="status.last_report.hits?.length">
            <div v-for="(hit, i) in status.last_report.hits" :key="i" class="d-flex align-center py-1" style="border-bottom:1px solid rgba(0,0,0,0.08)">
              <div class="flex-grow-1">{{ hit.name }}<span v-if="hit.season" class="text-caption text-medium-emphasis"> S{{ hit.season }}</span></div>
              <VChip size="small" :color="hit.action === 'delete' ? 'error' : 'warning'">
                {{ hit.action === 'delete' ? '已删除' : '已暂停' }}
              </VChip>
            </div>
          </div>
          <div v-else class="text-caption text-medium-emphasis">暂无命中记录</div>
        </VCardText>
        <VCardText v-else class="text-caption text-medium-emphasis">尚未执行过扫描</VCardText>
      </VCard>
    </template>
  </div>
</template>
