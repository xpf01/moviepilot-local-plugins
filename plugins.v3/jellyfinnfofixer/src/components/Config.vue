<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'JellyfinNfoFixer' },
  initialConfig: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['save', 'close'])
const saving = ref(false)
const message = reactive({ text: '', type: 'info' })

const defaults = {
  enabled: false,
  movie_library_dirs: '/media/电影',
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
      movie_library_dirs: String(config.movie_library_dirs || ''),
    }
    const response = await props.api.put(`plugin/${props.pluginId || 'JellyfinNfoFixer'}`, payload)
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
      <VIcon icon="mdi-file-document-check-outline" color="primary" class="me-2" />
      <div class="text-h6">Jellyfin Nfo命名修复配置</div>
      <VSpacer />
      <VBtn icon="mdi-content-save" variant="text" color="success" :loading="saving" title="保存配置" @click="saveConfig" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider class="mb-4" />
    <VAlert v-if="message.text" :type="message.type" variant="tonal" density="compact" class="mb-4">{{ message.text }}</VAlert>
    <VAlert type="info" variant="tonal" density="compact" class="mb-4">
      启用后监听元数据刮削完成事件，自动生成 movie.nfo；如需修正存量，请使用详情页「立即全库补齐」。
    </VAlert>
    <VRow dense>
      <VCol cols="12"><VSwitch v-model="config.enabled" label="启用插件" color="success" hide-details /></VCol>
      <VCol cols="12">
        <VTextarea
          v-model="config.movie_library_dirs"
          label="电影库目录（每行一个，用于全库补齐）"
          rows="5"
          variant="outlined"
          hint="例如 /media/电影"
          persistent-hint
        />
      </VCol>
    </VRow>
    <div class="d-flex justify-end mt-4"><VBtn color="primary" :loading="saving" @click="saveConfig">保存配置</VBtn></div>
  </div>
</template>

