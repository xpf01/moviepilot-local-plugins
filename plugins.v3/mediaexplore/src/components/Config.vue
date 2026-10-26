<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'MediaExplore' },
  initialConfig: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['save', 'close'])
const saving = ref(false)
const message = reactive({ text: '', type: 'info' })

const MODULES = [
  { key: 'tencentvideo', label: '腾讯视频' },
  { key: 'bilibili', label: '哔哩哔哩' },
  { key: 'cctv', label: 'CCTV' },
  { key: 'mangguo', label: '芒果TV' },
  { key: 'bangumidaily', label: 'Bangumi每日放送' },
  { key: 'migu', label: '咪咕视频' },
]

const defaults = {
  tencentvideo_enabled: false,
  bilibili_enabled: false,
  cctv_enabled: false,
  mangguo_enabled: false,
  bangumidaily_enabled: false,
  migu_enabled: false,
  iqiyi_enabled: false,
  iqiyi_cookie: '',
  iqiyi_refresh_cron: '',
  maoyan_enabled: false,
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
    const payload = {}
    for (const m of MODULES) payload[`${m.key}_enabled`] = Boolean(config[`${m.key}_enabled`])
    payload.iqiyi_enabled = Boolean(config.iqiyi_enabled)
    payload.iqiyi_cookie = String(config.iqiyi_cookie || '')
    payload.iqiyi_refresh_cron = String(config.iqiyi_refresh_cron || '')
    payload.maoyan_enabled = Boolean(config.maoyan_enabled)
    const response = await props.api.put(`plugin/${props.pluginId || 'MediaExplore'}`, payload)
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
      <VIcon icon="mdi-compass-outline" color="primary" class="me-2" />
      <div class="text-h6">媒体探索聚合配置</div>
      <VSpacer />
      <VBtn icon="mdi-content-save" variant="text" color="success" :loading="saving" title="保存配置" @click="saveConfig" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider class="mb-4" />
    <VAlert v-if="message.text" :type="message.type" variant="tonal" density="compact" class="mb-4">{{ message.text }}</VAlert>

    <VCard variant="outlined" class="mb-4">
      <VCardTitle class="text-subtitle-1">探索源开关</VCardTitle>
      <VCardText>
        <VRow dense>
          <VCol v-for="m in MODULES" :key="m.key" cols="12" md="4">
            <VSwitch v-model="config[`${m.key}_enabled`]" :label="`启用${m.label}探索源`" hide-details />
          </VCol>
          <VCol cols="12" md="4"><VSwitch v-model="config.iqiyi_enabled" label="启用爱奇艺探索源" hide-details /></VCol>
          <VCol cols="12" md="4"><VSwitch v-model="config.maoyan_enabled" label="启用猫眼TOP30探索源" hide-details /></VCol>
        </VRow>
      </VCardText>
    </VCard>

    <VCard variant="outlined" class="mb-4">
      <VCardTitle class="text-subtitle-1">爱奇艺配置</VCardTitle>
      <VCardText>
        <VTextField
          v-model="config.iqiyi_cookie"
          label="爱奇艺 Cookie（可选）"
          variant="outlined"
          hint="留空则由 CloakBrowser 自动获取；失效时可手动填入 Cookie"
          persistent-hint
        />
        <VTextField
          v-model="config.iqiyi_refresh_cron"
          label="Cookie 定时刷新周期（Cron 表达式，可选）"
          variant="outlined"
          hint="例如 0 */2 * * *（每 2 小时）"
          persistent-hint
        />
      </VCardText>
    </VCard>

    <div class="d-flex justify-end mt-4"><VBtn color="primary" :loading="saving" @click="saveConfig">保存配置</VBtn></div>
  </div>
</template>

