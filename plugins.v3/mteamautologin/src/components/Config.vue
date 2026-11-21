<script setup>
import { onMounted, reactive, ref } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'MTeamAutoLogin' },
  initialConfig: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['save', 'close'])
const saving = ref(false)
const showPassword = ref(false)
const message = reactive({ text: '', type: 'info' })

const defaults = {
  enabled: false,
  cron: '17 8 * * *',
  home_url: 'https://kp.m-team.cc/',
  login_url: 'https://kp.m-team.cc/login',
  username: '',
  password: '',
  email: '',
  totp_secret: '',
  notify_success: false,
  use_proxy: false,
  onlyonce: false,
  code_wait: 600,
  retry_interval: 20,
  retry_times: 3,
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
  if (config.enabled && (!config.username || !config.password)) {
    showMessage('启用前请先填写馒头用户名与密码', 'error')
    return
  }
  const totp = String(config.totp_secret || '').replace(/[\s-]/g, '').toUpperCase()
  if (totp && !/^[A-Z2-7]+=*$/.test(totp)) {
    showMessage('OTP 密钥格式不对：只允许字母 A-Z 和数字 2-7，请从二维码下方的纯文本复制', 'error')
    return
  }
  if (totp && totp.replace(/=+$/, '').length < 16) {
    showMessage('OTP 密钥长度偏短（常见 16 或 32 位），请确认是否复制完整', 'error')
    return
  }
  saving.value = true
  try {
    const payload = {
      enabled: Boolean(config.enabled),
      cron: String(config.cron || defaults.cron).trim(),
      home_url: String(config.home_url || defaults.home_url).trim(),
      login_url: String(config.login_url || defaults.login_url).trim(),
      username: String(config.username || '').trim(),
      password: String(config.password || ''),
      email: String(config.email || '').trim(),
      totp_secret: String(config.totp_secret || '').replace(/[\s-]/g, '').toUpperCase(),
      notify_success: Boolean(config.notify_success),
      use_proxy: Boolean(config.use_proxy),
      onlyonce: Boolean(config.onlyonce),
      code_wait: Number(config.code_wait) > 0 ? Math.floor(Number(config.code_wait)) : defaults.code_wait,
      retry_interval: Number(config.retry_interval) > 0 ? Math.floor(Number(config.retry_interval)) : defaults.retry_interval,
      retry_times: Number(config.retry_times) >= 0 ? Math.floor(Number(config.retry_times)) : defaults.retry_times,
    }
    const response = await props.api.put(`plugin/${props.pluginId || 'MTeamAutoLogin'}`, payload)
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
  const incoming = props.initialConfig || {}
  Object.assign(config, defaults)
  for (const key of Object.keys(defaults)) {
    if (incoming[key] !== undefined && incoming[key] !== null) config[key] = incoming[key]
  }
})
</script>

<template>
  <div class="pa-4">
    <VToolbar density="comfortable" color="transparent" class="px-0">
      <VIcon icon="mdi-account-key" color="primary" class="me-2" />
      <div class="text-h6">馒头自动登录保活配置</div>
      <VSpacer />
      <VBtn icon="mdi-content-save" variant="text" color="success" :loading="saving" title="保存配置" @click="saveConfig" />
      <VBtn icon="mdi-close" variant="text" title="关闭" @click="emit('close')" />
    </VToolbar>
    <VDivider class="mb-4" />
    <VAlert v-if="message.text" :type="message.type" variant="tonal" density="compact" class="mb-4">{{ message.text }}</VAlert>
    <VAlert type="info" variant="tonal" density="compact" class="mb-4">
      馒头 40 天保活只认「用浏览器存取网页」，API 访问和做种都不算。插件每天用真实浏览器存取一次；
      站点强制登入验证码且每台设备 30 天有效，因此浏览器使用持久化身份。
      填了 OTP 密钥后验证全自动、永不打扰；不填则到期时自动发邮箱验证码并通知你手动填一次。
    </VAlert>

    <VRow dense>
      <VCol cols="12" md="3">
        <VSwitch v-model="config.enabled" label="启用插件" color="success" hide-details />
      </VCol>
      <VCol cols="12" md="3">
        <VSwitch v-model="config.notify_success" label="成功也通知" color="primary" hide-details />
      </VCol>
      <VCol cols="12" md="3">
        <VSwitch v-model="config.use_proxy" label="浏览器走系统代理" color="info" hide-details />
      </VCol>
      <VCol cols="12" md="3">
        <VSwitch v-model="config.onlyonce" label="保存后立即登录一次" color="warning" hide-details />
      </VCol>
    </VRow>

    <VRow dense class="mt-4">
      <VCol cols="12" md="6">
        <VTextField
          v-model="config.email"
          label="注册邮箱（验证码发到这个邮箱）"
          placeholder="与馒头账号绑定的 Gmail"
          variant="outlined"
          density="compact"
          color="primary"
          hide-details
          persistent-hint
          hint="必填。验证到期时插件用它在登录页点「获取验证码」"
        />
      </VCol>
      <VCol cols="12" md="6">
        <VTextField
          v-model="config.username"
          label="馒头用户名"
          placeholder="登录用户名"
          variant="outlined"
          density="compact"
          autocomplete="off"
          hide-details
        />
      </VCol>
      <VCol cols="12" md="6">
        <VTextField
          v-model="config.password"
          label="馒头密码"
          :type="showPassword ? 'text' : 'password'"
          :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
          variant="outlined"
          density="compact"
          autocomplete="new-password"
          hide-details
          @click:append-inner="showPassword = !showPassword"
        />
      </VCol>
      <VCol cols="12" md="6">
        <VTextField
          v-model="config.cron"
          label="执行周期（5 位 cron）"
          placeholder="17 8 * * *"
          variant="outlined"
          density="compact"
          hide-details
          persistent-hint
          hint="默认每天 08:17 存取一次"
        />
      </VCol>
      <VCol cols="12" md="6">
        <VTextField
          v-model="config.home_url"
          label="站点首页地址"
          placeholder="https://kp.m-team.cc/"
          variant="outlined"
          density="compact"
          hide-details
          persistent-hint
          hint="日常保活直接存取这个页面"
        />
      </VCol>
      <VCol cols="12" md="6">
        <VTextField
          v-model="config.login_url"
          label="登录页地址"
          placeholder="https://kp.m-team.cc/login"
          variant="outlined"
          density="compact"
          hide-details
          persistent-hint
          hint="站点换域名时改这里"
        />
      </VCol>
    </VRow>

    <VRow dense class="mt-4">
      <VCol cols="12" md="4">
        <VTextField
          v-model.number="config.code_wait"
          type="number"
          label="等待填入验证码（秒）"
          variant="outlined"
          density="compact"
          hide-details
          persistent-hint
          hint="默认 600 秒，过期按重试策略再来"
        />
      </VCol>
      <VCol cols="12" md="4">
        <VTextField
          v-model.number="config.retry_interval"
          type="number"
          label="补码重试间隔（分钟）"
          variant="outlined"
          density="compact"
          hide-details
          persistent-hint
          hint="默认 20 分钟，每次重试会重新发码"
        />
      </VCol>
      <VCol cols="12" md="4">
        <VTextField
          v-model.number="config.retry_times"
          type="number"
          label="每日补码重试次数"
          variant="outlined"
          density="compact"
          hide-details
          persistent-hint
          hint="默认 3 次，填 0 表示不自动重试"
        />
      </VCol>
      <VCol cols="12">
        <VCard variant="outlined" color="primary">
          <VCardTitle class="text-subtitle-1 d-flex align-center">
            <VIcon icon="mdi-shield-key" class="me-2" />验证方式选择（决定要不要你手动填码）
          </VCardTitle>
          <VCardText>
            <VAlert type="info" variant="tonal" density="compact" class="mb-3">
              馒头支持三种登录验证：<strong>邮箱验证码</strong>、<strong>OTP 验证器</strong>、Telegram Bot。
              填了下面的密钥就自动走 OTP，插件自己算码提交，<strong>永远不需要你手动填</strong>。
              不填则走邮箱验证码，验证到期时要你手动填一次（约 30 天一次）。
            </VAlert>
            <VTextField
              v-model="config.totp_secret"
              label="OTP 验证器密钥（Base32，强烈建议填写）"
              placeholder="例如 JBSWY3DPEHPK3PXP"
              variant="outlined"
              density="compact"
              color="primary"
              hide-details
              persistent-hint
              hint="填了它就不再需要邮箱验证码，也不会再打扰你"
            />
            <VExpansionPanels variant="accordion" class="mt-3">
              <VExpansionPanel>
                <VExpansionPanelTitle class="text-body-2">怎么获取这个密钥？点开看步骤</VExpansionPanelTitle>
                <VExpansionPanelText>
                  <ol class="text-body-2 ps-5" style="line-height:1.9">
                    <li>浏览器登录馒头网页，进入「控制台 → 安全設定 → 二級驗證」。</li>
                    <li>启用 OTP 二级验证，页面会显示二维码和一段 <strong>Base32 密钥</strong>（形如 JBSWY3DPEHPK3PXP）。</li>
                    <li>把这段密钥复制到上面的输入框，点保存。</li>
                    <li>二维码下方「无法扫描？」一类链接通常会直接显示纯文本密钥；只认字母 A-Z 和数字 2-7。</li>
                  </ol>
                  <VAlert type="warning" variant="tonal" density="compact" class="mt-2">
                    手机上的验证器 App 不用非得绑定，插件本身就是验证器。但建议同时用 App 扫一次二维码做备份，
                    以免日后换设备时拿不到密钥。
                  </VAlert>
                  <VAlert type="info" variant="tonal" density="compact" class="mt-2">
                    站点官方说明：若遗失 OTP 二级验证，仍可用「密码 + 邮箱验证」登录，
                    再到控制台自行关闭，不会因此锁死账号。
                  </VAlert>
                </VExpansionPanelText>
              </VExpansionPanel>
            </VExpansionPanels>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <VAlert type="warning" variant="tonal" density="compact" class="mt-4">
      不需要填邮箱密码或 IMAP 授权码：插件只在登录页点「获取验证码」，验证码由你从邮箱看到后手动填入插件页面。
    </VAlert>
  </div>
</template>
