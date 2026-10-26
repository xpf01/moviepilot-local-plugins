<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'SeriesOrganizer' },
  initialConfig: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['save', 'close'])
const saving = ref(false)
const message = reactive({ text: '', type: 'info' })

const defaults = {
  enabled: false,
  notify: true,
  dry_run: false,
  series_map: '',
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
      notify: Boolean(config.notify),
      dry_run: Boolean(config.dry_run),
      series_map: String(config.series_map || ''),
    }
    const response = await props.api.put(`plugin/${props.pluginId || 'SeriesOrganizer'}`, payload)
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
      <VIcon icon="mdi-folder-multiple" color="primary" class="me-2" />
      <div class="text-h6">系列自动归组配置</div>
      <VSpacer />
      <VBtn icon="mdi-content-save" variant="text" color="success" :loading="saving" title="保存配置" @click="saveConfig" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider class="mb-4" />
    <VAlert v-if="message.text" :type="message.type" variant="tonal" density="compact" class="mb-4">{{ message.text }}</VAlert>
    <VAlert type="info" variant="tonal" density="compact" class="mb-4">
      整理完成后自动将同系列电影归入中文系列名父文件夹，仅在同一分类内归组、不跨分类。
    </VAlert>
    <VRow dense>
      <VCol cols="12"><VSwitch v-model="config.enabled" label="启用插件" color="success" hide-details /></VCol>
      <VCol cols="12"><VSwitch v-model="config.notify" label="未匹配的疑似续集发送提示" hide-details /></VCol>
      <VCol cols="12"><VSwitch v-model="config.dry_run" label="仅演练不实际移动（调试用）" color="warning" hide-details /></VCol>
      <VCol cols="12">
        <VTextarea
          v-model="config.series_map"
          label="系列映射表（每行一条：前缀:系列名）"
          rows="16"
          variant="outlined"
          hint="例如：速度与激情:速度与激情"
          persistent-hint
        />
      </VCol>
    </VRow>
    <div class="d-flex justify-end mt-4"><VBtn color="primary" :loading="saving" @click="saveConfig">保存配置</VBtn></div>
  </div>
</template>

