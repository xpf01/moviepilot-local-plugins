<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'TpdbScraper' },
  initialConfig: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['save', 'close'])
const saving = ref(false)
const message = reactive({ text: '', type: 'info' })

const defaults = {
  enabled: false,
  api_token: '',
  library_dirs: '/media/XXX',
  overwrite_nfo: false,
  download_poster: true,
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
  if (config.enabled && !String(config.api_token || '').trim()) {
    showMessage('启用插件前请填写 ThePornDB API Token', 'error')
    return
  }
  saving.value = true
  try {
    const payload = {
      enabled: Boolean(config.enabled),
      api_token: String(config.api_token || '').trim(),
      library_dirs: String(config.library_dirs || '').trim(),
      overwrite_nfo: Boolean(config.overwrite_nfo),
      download_poster: Boolean(config.download_poster),
    }
    const response = await props.api.put(`plugin/${props.pluginId || 'TpdbScraper'}`, payload)
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

async function scrapeNow() {
  if (typeof props.api?.post !== 'function') {
    showMessage('当前 MoviePilot 未提供刮削触发接口', 'error')
    return
  }
  try {
    const response = await props.api.post(`plugin/${props.pluginId || 'TpdbScraper'}/scrape_now`, {})
    const result = response?.data ?? response
    if (result?.success === false) throw new Error(result.message || '刮削失败')
    const data = result?.data ?? {}
    showMessage(`刮削完成：共 ${data.total ?? 0}，命中 ${data.matched ?? 0}，失败 ${data.failed ?? 0}`, 'success')
  } catch (error) {
    showMessage(error?.message || '刮削失败', 'error')
  }
}

onMounted(() => {
  Object.assign(config, defaults, props.initialConfig || {})
})
</script>

<template>
  <div class="pa-4">
    <VToolbar density="comfortable" color="transparent" class="px-0">
      <VIcon icon="mdi-movie-search" color="primary" class="me-2" />
      <div class="text-h6">ThePornDB 成人刮削配置</div>
      <VSpacer />
      <VBtn icon="mdi-content-save" variant="text" color="success" :loading="saving" title="保存配置" @click="saveConfig" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider class="mb-4" />
    <VAlert v-if="message.text" :type="message.type" variant="tonal" density="compact" class="mb-4">{{ message.text }}</VAlert>
    <VAlert type="info" variant="tonal" density="compact" class="mb-4">
      本插件在 MoviePilot 端调用 ThePornDB 刮削成人内容元数据，NFO 落盘并下载海报；Jellyfin 侧保持只读，扫描即可读取。
    </VAlert>
    <VRow dense>
      <VCol cols="12"><VSwitch v-model="config.enabled" label="启用插件" color="success" hide-details /></VCol>
      <VCol cols="12">
        <VTextField
          v-model="config.api_token"
          label="ThePornDB API Token"
          type="password"
          variant="outlined"
          hint="在 theporndb.net 的 API Tokens 页创建，需 read 权限。"
          persistent-hint
        />
      </VCol>
      <VCol cols="12">
        <VTextarea
          v-model="config.library_dirs"
          label="媒体库目录（每行一个）"
          rows="4"
          variant="outlined"
          hint="例如 /media/XXX"
          persistent-hint
        />
      </VCol>
      <VCol cols="12"><VSwitch v-model="config.overwrite_nfo" label="覆盖已有 movie.nfo" color="warning" hide-details /></VCol>
      <VCol cols="12"><VSwitch v-model="config.download_poster" label="下载海报 poster.jpg" color="success" hide-details /></VCol>
    </VRow>
    <div class="d-flex justify-end mt-4"><VBtn color="primary" :loading="saving" @click="saveConfig">保存配置</VBtn></div>
  </div>
</template>
