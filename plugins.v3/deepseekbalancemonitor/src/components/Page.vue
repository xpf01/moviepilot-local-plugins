<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'DeepSeekBalanceMonitor' },
})

const emit = defineEmits(['close'])
const loading = ref(false)
const running = ref(false)
const message = reactive({ text: '', type: 'info' })
const status = reactive({
  enabled: false,
  alerted: false,
  threshold: 5.0,
  last_report: '',
  balance: {},
  top_up_url: 'https://platform.deepseek.com/top_up',
  usage_url: 'https://platform.deepseek.com/usage',
})

function showMessage(text, type = 'info') {
  message.text = text
  message.type = type
  if (text) setTimeout(() => { if (message.text === text) message.text = '' }, 4000)
}

function fmt(value) {
  const n = Number(value)
  if (Number.isNaN(n)) return '—'
  return n.toFixed(4)
}

async function loadStatus() {
  loading.value = true
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'DeepSeekBalanceMonitor'}/status`)
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
    const response = await props.api.post(`plugin/${props.pluginId || 'DeepSeekBalanceMonitor'}/check_now`, {})
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

function openUrl(url) {
  if (url) window.open(url, '_blank')
}

onMounted(loadStatus)
</script>

<template>
  <div class="pa-4">
    <VToolbar density="comfortable" color="transparent" class="px-0">
      <VIcon icon="mdi-currency-cny" color="primary" class="me-2" />
      <div class="text-h6">DeepSeek余额监控</div>
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
      <VAlert :type="status.alerted ? 'warning' : 'success'" variant="tonal" density="compact" class="mb-4">
        告警状态：{{ status.alerted ? '已告警（欠费或低于阈值）' : '正常' }}
      </VAlert>

      <!-- 余额明细 + 告警阈值 -->
      <VRow dense>
        <VCol cols="12" md="3">
          <VCard variant="outlined" class="text-center">
            <VCardText>
              <div class="text-caption text-grey">总可用余额</div>
              <div class="text-h5">{{ fmt(status.balance?.total_balance) }} <span class="text-subtitle-2">{{ status.balance?.currency || '' }}</span></div>
            </VCardText>
          </VCard>
        </VCol>
        <VCol cols="12" md="3">
          <VCard variant="outlined" class="text-center">
            <VCardText>
              <div class="text-caption text-grey">充值余额</div>
              <div class="text-h5">{{ fmt(status.balance?.topped_up_balance) }} <span class="text-subtitle-2">{{ status.balance?.currency || '' }}</span></div>
            </VCardText>
          </VCard>
        </VCol>
        <VCol cols="12" md="3">
          <VCard variant="outlined" class="text-center">
            <VCardText>
              <div class="text-caption text-grey">赠金</div>
              <div class="text-h5">{{ fmt(status.balance?.granted_balance) }} <span class="text-subtitle-2">{{ status.balance?.currency || '' }}</span></div>
            </VCardText>
          </VCard>
        </VCol>
        <VCol cols="12" md="3">
          <VCard variant="outlined" class="text-center">
            <VCardText>
              <div class="text-caption text-grey">告警阈值</div>
              <div class="text-h5">{{ fmt(status.threshold) }} <span class="text-subtitle-2">{{ status.balance?.currency || '' }}</span></div>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>

      <VCard variant="outlined" class="mt-3">
        <VCardText>
          <div class="text-subtitle-2 mb-1">最近余额报告</div>
          <div class="text-body-2">{{ status.last_report || '尚未执行检查' }}</div>
        </VCardText>
      </VCard>

      <!-- 消费/请求次数/Token 用量：官方无 API，提供后台看板跳转 -->
      <VAlert type="info" variant="tonal" density="compact" class="mt-3 mb-0">
        消费金额、API 请求次数、Token 用量官方未提供 API，请在用量看板中查看。
      </VAlert>

      <div class="d-flex flex-wrap justify-end mt-4 ga-2">
        <VBtn color="primary" prepend-icon="mdi-play" :loading="running" @click="checkNow">立即检查</VBtn>
        <VBtn color="secondary" prepend-icon="mdi-chart-box" @click="openUrl(status.usage_url)">用量看板</VBtn>
        <VBtn color="success" prepend-icon="mdi-cash-plus" @click="openUrl(status.top_up_url)">前往充值</VBtn>
      </div>
    </template>
  </div>
</template>
