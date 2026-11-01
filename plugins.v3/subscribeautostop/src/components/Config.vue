<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'SubscribeAutoStop' },
  initialConfig: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['save', 'close'])
const saving = ref(false)
const message = reactive({ text: '', type: 'info' })

const defaults = {
  enabled: false,
  cron: '0 3 * * *',
  action: 'pause',
  notify: false,
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
      cron: String(config.cron || '0 3 * * *'),
      action: String(config.action || 'pause'),
      notify: Boolean(config.notify),
    }
    const response = await props.api.put(`plugin/${props.pluginId || 'SubscribeAutoStop'}`, payload)
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
      <VIcon icon="mdi-auto-download" color="primary" class="me-2" />
      <div class="text-h6">订阅入库自停配置</div>
      <VSpacer />
      <VBtn icon="mdi-content-save" variant="text" color="success" :loading="saving" title="保存配置" @click="saveConfig" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider class="mb-4" />
    <VAlert v-if="message.text" :type="message.type" variant="tonal" density="compact" class="mb-4">{{ message.text }}</VAlert>
    <VAlert type="info" variant="tonal" density="compact" class="mb-4">
      定时扫描「订阅中」的影片是否已完整入库：电影整部、电视剧整季全齐才命中，命中后按下方动作暂停或删除。
    </VAlert>
    <VRow dense>
      <VCol cols="12"><VSwitch v-model="config.enabled" label="启用插件" color="success" hide-details /></VCol>
      <VCol cols="12">
        <VTextField
          v-model="config.cron"
          label="定时表达式（5 位 cron）"
          placeholder="0 3 * * *"
          variant="outlined"
          hint="例如 0 3 * * * 表示每天凌晨 3 点执行一次"
          persistent-hint
        />
      </VCol>
      <VCol cols="12">
        <VSelect
          v-model="config.action"
          label="命中动作"
          :items="[
            { title: '暂停订阅（可手动恢复）', value: 'pause' },
            { title: '删除订阅（不可恢复）', value: 'delete' },
          ]"
          variant="outlined"
        />
      </VCol>
      <VCol cols="12"><VSwitch v-model="config.notify" label="命中后发送通知" hide-details /></VCol>
    </VRow>
    <div class="d-flex justify-end mt-4"><VBtn color="primary" :loading="saving" @click="saveConfig">保存配置</VBtn></div>
  </div>
</template>
