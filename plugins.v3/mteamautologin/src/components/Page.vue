<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'MTeamAutoLogin' },
})

const emit = defineEmits(['close'])
const loading = ref(false)
const triggering = ref(false)
const submitting = ref(false)
const codeInput = ref('')
const message = reactive({ text: '', type: 'info' })
const showTotpGuide = ref(false)
const status = reactive({
  enabled: false,
  cron: '',
  login_url: '',
  home_url: '',
  username: '',
  has_password: false,
  email: '',
  notify_success: false,
  use_proxy: false,
  code_wait: 600,
  retry_interval: 20,
  retry_times: 3,
  keepalive_days: 40,
  device_valid_days: 30,
  device_verified_at: '',
  device_days_since: null,
  device_expire_in: null,
  awaiting_code: false,
  code_requested_at: '',
  code_deadline: '',
  last_result: null,
  history: [],
  next_run: '',
})

let pollTimer = null

const lastSuccess = computed(() => Boolean(status.last_result?.success))
const statusColor = computed(() => (!status.last_result ? 'info' : (lastSuccess.value ? 'success' : 'error')))
const remaining = computed(() => status.last_result?.remaining)
const deviceExpire = computed(() => status.device_expire_in)
const deviceColor = computed(() => {
  if (deviceExpire.value === null || deviceExpire.value === undefined) return 'info'
  if (deviceExpire.value <= 1) return 'error'
  if (deviceExpire.value <= 3) return 'warning'
  return 'success'
})

function showMessage(text, type = 'info') {
  message.text = text
  message.type = type
  if (text) setTimeout(() => { if (message.text === text) message.text = '' }, 5000)
}

function api() {
  return props.api || {}
}

async function loadStatus() {
  loading.value = true
  try {
    const response = await api().get(`plugin/${props.pluginId || 'MTeamAutoLogin'}/status`)
    const result = response?.data ?? response
    if (result?.success !== false) Object.assign(status, result?.data ?? result ?? {})
  } catch (error) {
    /* 忽略状态读取失败 */
  } finally {
    loading.value = false
  }
}

async function post(path, body = {}) {
  const response = await api().post(`plugin/${props.pluginId || 'MTeamAutoLogin'}${path}`, body)
  return response?.data ?? response
}

async function loginNow() {
  triggering.value = true
  try {
    const result = await post('/login')
    if (result?.success === false) showMessage(result?.message || '触发登录失败', 'error')
    else {
      showMessage(result?.message || '已开始登录', 'success')
      setTimeout(loadStatus, 15000)
      startPolling()
    }
  } catch (error) {
    showMessage(error?.message || '触发登录失败', 'error')
  } finally {
    triggering.value = false
  }
}

async function reverify() {
  triggering.value = true
  try {
    const result = await post('/reverify')
    if (result?.success === false) showMessage(result?.message || '触发重新验证失败', 'error')
    else {
      showMessage(result?.message || '已开始重新验证', 'success')
      setTimeout(loadStatus, 15000)
      startPolling()
    }
  } catch (error) {
    showMessage(error?.message || '触发重新验证失败', 'error')
  } finally {
    triggering.value = false
  }
}

async function submitCode() {
  const code = String(codeInput.value || '').trim()
  if (!code) {
    showMessage('请先填入邮箱收到的验证码', 'error')
    return
  }
  submitting.value = true
  try {
    const result = await post('/code', { code })
    if (result?.success === false) showMessage(result?.message || '提交验证码失败', 'error')
    else {
      showMessage('验证码已提交，正在完成登录', 'success')
      codeInput.value = ''
      setTimeout(loadStatus, 8000)
      startPolling()
    }
  } catch (error) {
    showMessage(error?.message || '提交验证码失败', 'error')
  } finally {
    submitting.value = false
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(loadStatus, 10000)
  setTimeout(stopPolling, 180000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(() => {
  loadStatus()
  startPolling()
})
onUnmounted(stopPolling)
</script>

<template>
  <div class="pa-4">
    <VToolbar density="comfortable" color="transparent" class="px-0">
      <VIcon icon="mdi-account-key" color="primary" class="me-2" />
      <div class="text-h6">馒头自动登录保活</div>
      <VSpacer />
      <VBtn color="primary" variant="tonal" :loading="triggering" class="me-2" @click="loginNow">
        <VIcon icon="mdi-login" class="me-1" />立即登录
      </VBtn>
      <VBtn color="warning" variant="tonal" :loading="triggering" class="me-2" @click="reverify">
        <VIcon icon="mdi-shield-refresh" class="me-1" />重新验证
      </VBtn>
      <VBtn icon="mdi-refresh" variant="text" :loading="loading" title="刷新状态" @click="loadStatus" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider class="mb-4" />
    <VAlert v-if="message.text" :type="message.type" variant="tonal" density="compact" class="mb-4">{{ message.text }}</VAlert>

    <VAlert v-if="!status.enabled" type="warning" variant="tonal" density="compact" class="mb-4">
      插件未启用，请在「配置」中启用并填写用户名与密码。
    </VAlert>
    <VAlert v-else-if="!status.has_password" type="error" variant="tonal" density="compact" class="mb-4">
      未检测到密码，请先在「配置」中补全凭据。
    </VAlert>

    <VAlert v-if="status.enabled && status.has_password && !status.has_totp" type="info" variant="tonal" density="compact" class="mb-4">
      <div class="d-flex align-center flex-wrap" style="gap:12px">
        <VIcon icon="mdi-shield-key-outline" />
        <span class="flex-grow-1">
          当前使用「邮箱验证码」：验证到期时需要你手动填一次码（约 30 天一次）。
          填入 OTP 密钥后可改为全自动，永不再打扰。
        </span>
        <VBtn size="small" variant="tonal" color="primary" @click="showTotpGuide = !showTotpGuide">
          {{ showTotpGuide ? '收起' : '如何开启' }}
        </VBtn>
      </div>
      <ol v-if="showTotpGuide" class="text-body-2 ps-5 mt-3" style="line-height:1.9">
        <li>浏览器登录馒头网页 → 控制台 → 安全設定 → 二級驗證。</li>
        <li>启用 OTP，复制二维码下方那段 Base32 密钥。</li>
        <li>到本插件「配置」页填进「OTP 验证器密钥」并保存。</li>
        <li>此后验证码由插件自动计算提交，不再需要人工介入。</li>
      </ol>
    </VAlert>

    <VCard v-if="status.awaiting_code" variant="outlined" class="mb-4" border color="warning">
      <VCardTitle class="text-subtitle-1">
        <VIcon icon="mdi-email-fast" color="warning" class="me-2" />需要填写邮箱验证码
      </VCardTitle>
      <VCardText>
        <div class="text-body-2 mb-3">
          插件已自动点「获取验证码」，请到
          <strong>{{ status.email || '注册邮箱' }}</strong>
          查收（含垃圾邮件箱）。请求时间 {{ status.code_requested_at || '-' }}，
          本次等待截止 {{ status.code_deadline || '-' }}。
        </div>
        <div class="d-flex align-center" style="gap:12px;flex-wrap:wrap">
          <VTextField
            v-model="codeInput"
            label="6 位邮箱验证码"
            placeholder="填入邮件中的验证码"
            variant="outlined"
            density="compact"
            hide-details
            style="max-width:240px"
            @keyup.enter="submitCode"
          />
          <VBtn color="warning" :loading="submitting" @click="submitCode">提交验证码</VBtn>
        </div>
        <div class="text-caption text-medium-emphasis mt-3">
          不方便现在填？直接关掉即可。插件会在 {{ status.retry_interval }} 分钟后自动重新发码，
          每天最多 {{ status.retry_times }} 次；你也可以随时点右上「立即登录」重新发码，
          40 天保活期内任何方便的时候补上都来得及。
        </div>
      </VCardText>
    </VCard>

    <VRow dense>
      <VCol cols="12" md="3">
        <VCard variant="outlined">
          <VCardText>
            <div class="text-caption text-medium-emphasis">执行周期</div>
            <div class="text-h6">{{ status.cron || '-' }}</div>
            <div class="text-caption text-medium-emphasis">下次 {{ status.next_run || '未排期' }}</div>
          </VCardText>
        </VCard>
      </VCol>
      <VCol cols="12" md="3">
        <VCard variant="outlined">
          <VCardText>
            <div class="text-caption text-medium-emphasis">最近结果</div>
            <div class="text-h6" :class="`text-${statusColor}`">
              {{ status.last_result ? (lastSuccess ? '成功' : '失败') : '尚未执行' }}
            </div>
            <div class="text-caption text-medium-emphasis">{{ status.last_result?.at || '-' }}</div>
          </VCardText>
        </VCard>
      </VCol>
      <VCol cols="12" md="3">
        <VCard variant="outlined">
          <VCardText>
            <div class="text-caption text-medium-emphasis">设备受信剩余</div>
            <div class="text-h6" :class="`text-${deviceColor}`">
              {{ deviceExpire === null || deviceExpire === undefined ? '待确认' : `${deviceExpire} 天` }}
            </div>
            <div class="text-caption text-medium-emphasis">
              已验证 {{ status.device_verified_at || '未记录' }} / 共 {{ status.device_valid_days }} 天
            </div>
          </VCardText>
        </VCard>
      </VCol>
      <VCol cols="12" md="3">
        <VCard variant="outlined">
          <VCardText>
            <div class="text-caption text-medium-emphasis">距 {{ status.keepalive_days }} 天保活线</div>
            <div class="text-h6">{{ remaining === null || remaining === undefined ? '待复核' : `${remaining} 天` }}</div>
            <div class="text-caption text-medium-emphasis">站点最近浏览 {{ status.last_result?.last_browse || '-' }}</div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <VCard variant="outlined" class="mt-4">
      <VCardTitle class="text-subtitle-1">最近一次执行</VCardTitle>
      <VCardText v-if="status.last_result">
        <div class="text-body-2 mb-1">执行时间：{{ status.last_result.at || '-' }}（耗时 {{ status.last_result.seconds ?? '-' }} 秒）</div>
        <div class="text-body-2 mb-1">结果：{{ status.last_result.message || '-' }}</div>
        <div v-if="status.last_result.verify" class="text-body-2 mb-1">站点复核：{{ status.last_result.verify }}</div>
        <div class="text-caption text-medium-emphasis">
          账号：{{ status.username || '-' }} · 邮箱：{{ status.email || '未填' }} ·
          验证方式：{{ status.has_totp ? 'OTP 自动（无需人工）' : '邮箱验证码（到期需手动填）' }} ·
          代理：{{ status.use_proxy ? '走系统代理' : '直连' }}
        </div>
        <VAlert v-if="status.last_result.screenshot" type="info" variant="tonal" density="compact" class="mt-3">
          现场截图已保存为插件数据目录下的 {{ status.last_result.screenshot }}，可下载排查。
        </VAlert>
      </VCardText>
      <VCardText v-else class="text-caption text-medium-emphasis">尚未执行过登录</VCardText>
    </VCard>

    <VCard variant="outlined" class="mt-4">
      <VCardTitle class="text-subtitle-1">登录历史</VCardTitle>
      <VCardText v-if="status.history?.length">
        <div
          v-for="(item, i) in status.history"
          :key="i"
          class="d-flex align-start py-2"
          style="border-bottom:1px solid rgba(128,128,128,0.16)"
        >
          <VIcon :icon="item.success ? 'mdi-check-circle' : 'mdi-alert-circle'" :color="item.success ? 'success' : 'error'" size="small" class="me-2 mt-1" />
          <div class="flex-grow-1">
            <div class="text-body-2">{{ item.at || '-' }}<span v-if="item.mode" class="text-caption text-medium-emphasis"> · {{ item.mode }}</span></div>
            <div class="text-caption text-medium-emphasis">{{ item.message || '-' }}</div>
            <div v-if="item.verify" class="text-caption text-medium-emphasis">{{ item.verify }}</div>
          </div>
          <VChip v-if="item.remaining !== null && item.remaining !== undefined" size="small" variant="tonal" color="primary">
            剩 {{ item.remaining }} 天
          </VChip>
        </div>
      </VCardText>
      <VCardText v-else class="text-caption text-medium-emphasis">暂无历史记录</VCardText>
    </VCard>
  </div>
</template>
