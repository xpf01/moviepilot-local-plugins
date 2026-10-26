<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'IsoRemuxOrganize' },
  initialConfig: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['save', 'close'])
const saving = ref(false)
const message = reactive({ text: '', type: 'info' })

const defaults = {
  enabled: false,
  scan_root: '/media/影视下载',
  interval: 1800,
  timeout: 21600,
  notify: true,
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
      scan_root: String(config.scan_root || '').trim(),
      interval: Number(config.interval) || 1800,
      timeout: Number(config.timeout) || 21600,
      notify: Boolean(config.notify),
    }
    const response = await props.api.put(`plugin/${props.pluginId || 'IsoRemuxOrganize'}`, payload)
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
      <VIcon icon="mdi-disc" color="primary" class="me-2" />
      <div class="text-h6">ISO原盘转封装配置</div>
      <VSpacer />
      <VBtn icon="mdi-content-save" variant="text" color="success" :loading="saving" title="保存配置" @click="saveConfig" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider class="mb-4" />
    <VAlert v-if="message.text" :type="message.type" variant="tonal" density="compact" class="mb-4">{{ message.text }}</VAlert>
    <VAlert type="info" variant="tonal" density="compact" class="mb-4">
      仅处理 .iso 单文件；挂载后定位最大 m2ts 无损转 MKV，原始 ISO 保留。
    </VAlert>
    <VRow dense>
      <VCol cols="12"><VSwitch v-model="config.enabled" label="启用插件" color="success" hide-details /></VCol>
      <VCol cols="12">
        <VTextField v-model="config.scan_root" label="扫描根目录" variant="outlined" hint="例如 /media/影视下载" persistent-hint />
      </VCol>
      <VCol cols="12" md="6">
        <VTextField v-model.number="config.interval" label="定时扫描间隔（秒）" type="number" variant="outlined" hint="最小 300" persistent-hint />
      </VCol>
      <VCol cols="12" md="6">
        <VTextField v-model.number="config.timeout" label="转封装超时（秒）" type="number" variant="outlined" hint="最小 60" persistent-hint />
      </VCol>
      <VCol cols="12"><VSwitch v-model="config.notify" label="处理完成发送通知" hide-details /></VCol>
    </VRow>
    <div class="d-flex justify-end mt-4"><VBtn color="primary" :loading="saving" @click="saveConfig">保存配置</VBtn></div>
  </div>
</template>

