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
  tpdb_use_proxy: false,
  tpdb_proxy: 'http://192.168.1.2:7893',
  library_dirs: '/media/XXX',
  overwrite_nfo: false,
  download_poster: true,
  stashdb_enabled: false,
  stashdb_api_key: '',
  extra_stashbox_endpoints: '',
  stashbox_use_proxy: false,
  stashbox_proxy: 'http://192.168.1.2:7893',
  scrape_hour: 2,
  batch_size: 50,
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
      tpdb_use_proxy: Boolean(config.tpdb_use_proxy),
      tpdb_proxy: String(config.tpdb_proxy || '').trim(),
      library_dirs: String(config.library_dirs || '').trim(),
      overwrite_nfo: Boolean(config.overwrite_nfo),
      download_poster: Boolean(config.download_poster),
      stashdb_enabled: Boolean(config.stashdb_enabled),
      stashdb_api_key: String(config.stashdb_api_key || '').trim(),
      extra_stashbox_endpoints: String(config.extra_stashbox_endpoints || ''),
      stashbox_use_proxy: Boolean(config.stashbox_use_proxy),
      stashbox_proxy: String(config.stashbox_proxy || '').trim(),
      scrape_hour: Number(config.scrape_hour) || 2,
      batch_size: Number(config.batch_size) || 50,
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
        <VTextField v-model="config.api_token" label="ThePornDB API Token" type="password" variant="outlined" hint="在 theporndb.net 的 API Tokens 页创建，需 read 权限。" persistent-hint />
      </VCol>
      <VCol cols="12" md="6"><VSwitch v-model="config.tpdb_use_proxy" label="ThePornDB 主源走代理" hide-details /></VCol>
      <VCol cols="12" md="6"><VTextField v-model="config.tpdb_proxy" label="ThePornDB 代理地址" variant="outlined" placeholder="http://192.168.1.2:7893" /></VCol>
      <VCol cols="12">
        <VTextarea v-model="config.library_dirs" label="媒体库目录（每行一个）" rows="4" variant="outlined" hint="例如 /media/XXX" persistent-hint />
      </VCol>
      <VCol cols="12" md="6"><VSwitch v-model="config.overwrite_nfo" label="覆盖已有 movie.nfo" color="warning" hide-details /></VCol>
      <VCol cols="12" md="6"><VSwitch v-model="config.download_poster" label="下载海报 poster.jpg" color="success" hide-details /></VCol>
      <VCol cols="12" md="6"><VSwitch v-model="config.stashdb_enabled" label="启用 StashDB 补充源" hide-details /></VCol>
      <VCol cols="12" md="6"><VTextField v-model="config.stashdb_api_key" label="StashDB API Key" type="password" variant="outlined" hint="在 stashdb.org 个人页复制（可选）" persistent-hint /></VCol>
      <VCol cols="12">
        <VTextarea v-model="config.extra_stashbox_endpoints" label="额外备用 Stash-box 端点（每行一个，格式 端点|APIKey）" rows="3" variant="outlined" hint="https://fansdb.cc/graphql|你的key" persistent-hint />
      </VCol>
      <VCol cols="12" md="6"><VSwitch v-model="config.stashbox_use_proxy" label="Stash-box 补充源走代理" hide-details /></VCol>
      <VCol cols="12" md="6"><VTextField v-model="config.stashbox_proxy" label="Stash-box 代理地址" variant="outlined" placeholder="http://192.168.1.2:7893" /></VCol>
      <VCol cols="12" md="6"><VTextField v-model.number="config.scrape_hour" label="每日刮削时间（小时，0-23）" type="number" variant="outlined" hint="2 = 凌晨 2 点" persistent-hint /></VCol>
      <VCol cols="12" md="6"><VTextField v-model.number="config.batch_size" label="每轮刮削数量" type="number" variant="outlined" hint="每轮最多处理的条目数" persistent-hint /></VCol>
    </VRow>
    <div class="d-flex justify-end mt-4"><VBtn color="primary" :loading="saving" @click="saveConfig">保存配置</VBtn></div>
  </div>
</template>
