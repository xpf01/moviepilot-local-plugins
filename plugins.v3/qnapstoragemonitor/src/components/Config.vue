<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'QnapStorageMonitor' },
  initialConfig: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['save', 'close'])
const saving = ref(false)
const message = reactive({ text: '', type: 'info' })

const defaults = {
  enabled: false,
  host: '192.168.1.11',
  port: 22,
  username: '',
  password: '',
  interval_hours: 12,
  stop_threshold_gb: 500,
  resume_threshold_gb: 2000,
  auto_pause_download: true,
  monitor_all: false,
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
      host: String(config.host || '').trim(),
      port: Number(config.port) || 22,
      username: String(config.username || '').trim(),
      password: String(config.password || ''),
      interval_hours: Number(config.interval_hours) || 12,
      stop_threshold_gb: Number(config.stop_threshold_gb) || 500,
      resume_threshold_gb: Number(config.resume_threshold_gb) || 2000,
      auto_pause_download: Boolean(config.auto_pause_download),
      monitor_all: Boolean(config.monitor_all),
      onlyonce: Boolean(config.onlyonce),
    }
    const response = await props.api.put(`plugin/${props.pluginId || 'QnapStorageMonitor'}`, payload)
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
      <VIcon icon="mdi-database" color="primary" class="me-2" />
      <div class="text-h6">QNAP存储池监控配置</div>
      <VSpacer />
      <VBtn icon="mdi-content-save" variant="text" color="success" :loading="saving" title="保存配置" @click="saveConfig" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider class="mb-4" />
    <VAlert v-if="message.text" :type="message.type" variant="tonal" density="compact" class="mb-4">{{ message.text }}</VAlert>
    <VAlert type="info" variant="tonal" density="compact" class="mb-4">
      低于「停止下载阈值」暂停下载器任务（保留做种），高于「恢复下载阈值」自动恢复。仅支持 Transmission 下载器。
    </VAlert>
    <VRow dense>
      <VCol cols="12" md="6"><VSwitch v-model="config.enabled" label="启用插件" color="success" hide-details /></VCol>
      <VCol cols="12" md="6"><VSwitch v-model="config.onlyonce" label="立即运行一次" hide-details /></VCol>
      <VCol cols="12" md="6"><VTextField v-model="config.host" label="QNAP 地址" variant="outlined" placeholder="192.168.1.11" /></VCol>
      <VCol cols="12" md="6"><VTextField v-model.number="config.port" label="SSH 端口" type="number" variant="outlined" placeholder="22" /></VCol>
      <VCol cols="12" md="6"><VTextField v-model="config.username" label="SSH 用户名" variant="outlined" placeholder="admin" /></VCol>
      <VCol cols="12" md="6"><VTextField v-model="config.password" label="SSH 密码" type="password" variant="outlined" /></VCol>
      <VCol cols="12" md="4"><VTextField v-model.number="config.interval_hours" label="轮询间隔(小时)" type="number" variant="outlined" placeholder="12" /></VCol>
      <VCol cols="12" md="4"><VTextField v-model.number="config.stop_threshold_gb" label="停止下载阈值(GB)" type="number" variant="outlined" placeholder="500" /></VCol>
      <VCol cols="12" md="4"><VTextField v-model.number="config.resume_threshold_gb" label="恢复下载阈值(GB)" type="number" variant="outlined" placeholder="2000" /></VCol>
      <VCol cols="12" md="6"><VSwitch v-model="config.auto_pause_download" label="低于阈值时自动暂停下载" hide-details /></VCol>
      <VCol cols="12" md="6"><VSwitch v-model="config.monitor_all" label="监控全部存储池" hide-details /></VCol>
    </VRow>
    <div class="d-flex justify-end mt-4"><VBtn color="primary" :loading="saving" @click="saveConfig">保存配置</VBtn></div>
  </div>
</template>

