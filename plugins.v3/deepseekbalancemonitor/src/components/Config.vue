<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'DeepSeekBalanceMonitor' },
  initialConfig: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['save', 'close'])
const saving = ref(false)
const message = reactive({ text: '', type: 'info' })

const defaults = {
  enabled: false,
  interval_minutes: 60,
  threshold: 5.0,
  api_key: '',
  base_url: 'https://api.deepseek.com',
  balance_url: '',
  timeout: 20,
  use_proxy: false,
  onlyonce: false,
}

const config = reactive({ ...defaults })

function showMessage(text, type = 'info') {
  message.text = text
  message.type = type
  if (text) setTimeout(() => { if (message.text === text) message.text = '' }, 3500)
}

async function saveConfig() {
  if (typeof props.api?.put !== 'function') {
    showMessage('当前 MoviePilot 未提供配置保存接口', 'error')
    return
  }
  saving.value = true
  try {
    const payload = {
      enabled: Boolean(config.enabled),
      interval_minutes: Number(config.interval_minutes) || 60,
      threshold: Number(config.threshold) || 5.0,
      api_key: String(config.api_key || '').trim(),
      base_url: String(config.base_url || '').trim(),
      balance_url: String(config.balance_url || '').trim(),
      timeout: Number(config.timeout) || 20,
      use_proxy: Boolean(config.use_proxy),
      onlyonce: Boolean(config.onlyonce),
    }
    const response = await props.api.put(`plugin/${props.pluginId || 'DeepSeekBalanceMonitor'}`, payload)
    const result = response?.data ?? response
    if (result?.success === false) throw new Error(result.message || '保存配置失败')
    emit('save', payload)
    showMessage('配置已保存', 'success')
  } catch (error) {
    showMessage(error?.message || '保存配置失败', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  Object.assign(config, defaults, props.initialConfig || {})
})
</script>

<template>
  <div class="pa-4">
    <VToolbar density="comfortable" color="transparent" class="px-0">
      <VIcon icon="mdi-currency-cny" color="primary" class="me-2" />
      <div class="text-h6">DeepSeek余额监控配置</div>
      <VSpacer />
      <VBtn icon="mdi-content-save" variant="text" color="success" :loading="saving" title="保存配置" @click="saveConfig" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider class="mb-4" />
    <VAlert v-if="message.text" :type="message.type" variant="tonal" density="compact" class="mb-4">{{ message.text }}</VAlert>
    <VAlert type="info" variant="tonal" density="compact" class="mb-4">
      监控总可用余额（充值 + 赠金），低于阈值或账户欠费时通知告警，充值恢复后再次跌破才重新提醒。API Key 留空时自动复用系统 LLM 配置。
    </VAlert>
    <VRow dense>
      <VCol cols="12" md="6"><VSwitch v-model="config.enabled" label="启用插件" color="success" hide-details /></VCol>
      <VCol cols="12" md="6"><VSwitch v-model="config.onlyonce" label="立即运行一次" hide-details /></VCol>
      <VCol cols="12" md="4"><VTextField v-model.number="config.interval_minutes" label="轮询间隔(分钟)" type="number" variant="outlined" placeholder="60" /></VCol>
      <VCol cols="12" md="4"><VTextField v-model.number="config.threshold" label="告警阈值(余额)" type="number" variant="outlined" placeholder="5" /></VCol>
      <VCol cols="12" md="4"><VTextField v-model.number="config.timeout" label="请求超时(秒)" type="number" variant="outlined" placeholder="20" /></VCol>
      <VCol cols="12"><VTextField v-model="config.api_key" label="API Key（留空复用系统 LLM 配置）" type="password" variant="outlined" /></VCol>
      <VCol cols="12" md="6"><VTextField v-model="config.base_url" label="Base URL" variant="outlined" placeholder="https://api.deepseek.com" /></VCol>
      <VCol cols="12" md="6"><VTextField v-model="config.balance_url" label="余额接口（留空自动拼接 /user/balance）" variant="outlined" /></VCol>
      <VCol cols="12" md="6"><VSwitch v-model="config.use_proxy" label="使用系统代理访问" hide-details /></VCol>
    </VRow>
    <div class="d-flex justify-end mt-4"><VBtn color="primary" :loading="saving" @click="saveConfig">保存配置</VBtn></div>
  </div>
</template>
