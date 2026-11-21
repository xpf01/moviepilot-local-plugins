import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,createTextVNode:_createTextVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementBlock:_createElementBlock,withKeys:_withKeys,normalizeClass:_normalizeClass,renderList:_renderList,Fragment:_Fragment} = await importShared('vue');


const _hoisted_1 = { class: "pa-4" };
const _hoisted_2 = {
  class: "d-flex align-center flex-wrap",
  style: {"gap":"12px"}
};
const _hoisted_3 = {
  key: 0,
  class: "text-body-2 ps-5 mt-3",
  style: {"line-height":"1.9"}
};
const _hoisted_4 = { class: "text-body-2 mb-3" };
const _hoisted_5 = {
  class: "d-flex align-center",
  style: {"gap":"12px","flex-wrap":"wrap"}
};
const _hoisted_6 = { class: "text-caption text-medium-emphasis mt-3" };
const _hoisted_7 = { class: "text-h6" };
const _hoisted_8 = { class: "text-caption text-medium-emphasis" };
const _hoisted_9 = { class: "text-caption text-medium-emphasis" };
const _hoisted_10 = { class: "text-caption text-medium-emphasis" };
const _hoisted_11 = { class: "text-caption text-medium-emphasis" };
const _hoisted_12 = { class: "text-h6" };
const _hoisted_13 = { class: "text-caption text-medium-emphasis" };
const _hoisted_14 = { class: "text-body-2 mb-1" };
const _hoisted_15 = { class: "text-body-2 mb-1" };
const _hoisted_16 = {
  key: 0,
  class: "text-body-2 mb-1"
};
const _hoisted_17 = { class: "text-caption text-medium-emphasis" };
const _hoisted_18 = { class: "flex-grow-1" };
const _hoisted_19 = { class: "text-body-2" };
const _hoisted_20 = {
  key: 0,
  class: "text-caption text-medium-emphasis"
};
const _hoisted_21 = { class: "text-caption text-medium-emphasis" };
const _hoisted_22 = {
  key: 0,
  class: "text-caption text-medium-emphasis"
};

const {computed,onMounted,onUnmounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'MTeamAutoLogin' },
},
  emits: ['close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const loading = ref(false);
const triggering = ref(false);
const submitting = ref(false);
const codeInput = ref('');
const message = reactive({ text: '', type: 'info' });
const showTotpGuide = ref(false);
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
});

let pollTimer = null;

const lastSuccess = computed(() => Boolean(status.last_result?.success));
const statusColor = computed(() => (!status.last_result ? 'info' : (lastSuccess.value ? 'success' : 'error')));
const remaining = computed(() => status.last_result?.remaining);
const deviceExpire = computed(() => status.device_expire_in);
const deviceColor = computed(() => {
  if (deviceExpire.value === null || deviceExpire.value === undefined) return 'info'
  if (deviceExpire.value <= 1) return 'error'
  if (deviceExpire.value <= 3) return 'warning'
  return 'success'
});

function showMessage(text, type = 'info') {
  message.text = text;
  message.type = type;
  if (text) setTimeout(() => { if (message.text === text) message.text = ''; }, 5000);
}

function api() {
  return props.api || {}
}

async function loadStatus() {
  loading.value = true;
  try {
    const response = await api().get(`plugin/${props.pluginId || 'MTeamAutoLogin'}/status`);
    const result = response?.data ?? response;
    if (result?.success !== false) Object.assign(status, result?.data ?? result ?? {});
  } catch (error) {
    /* 忽略状态读取失败 */
  } finally {
    loading.value = false;
  }
}

async function post(path, body = {}) {
  const response = await api().post(`plugin/${props.pluginId || 'MTeamAutoLogin'}${path}`, body);
  return response?.data ?? response
}

async function loginNow() {
  triggering.value = true;
  try {
    const result = await post('/login');
    if (result?.success === false) showMessage(result?.message || '触发登录失败', 'error');
    else {
      showMessage(result?.message || '已开始登录', 'success');
      setTimeout(loadStatus, 15000);
      startPolling();
    }
  } catch (error) {
    showMessage(error?.message || '触发登录失败', 'error');
  } finally {
    triggering.value = false;
  }
}

async function reverify() {
  triggering.value = true;
  try {
    const result = await post('/reverify');
    if (result?.success === false) showMessage(result?.message || '触发重新验证失败', 'error');
    else {
      showMessage(result?.message || '已开始重新验证', 'success');
      setTimeout(loadStatus, 15000);
      startPolling();
    }
  } catch (error) {
    showMessage(error?.message || '触发重新验证失败', 'error');
  } finally {
    triggering.value = false;
  }
}

async function submitCode() {
  const code = String(codeInput.value || '').trim();
  if (!code) {
    showMessage('请先填入邮箱收到的验证码', 'error');
    return
  }
  submitting.value = true;
  try {
    const result = await post('/code', { code });
    if (result?.success === false) showMessage(result?.message || '提交验证码失败', 'error');
    else {
      showMessage('验证码已提交，正在完成登录', 'success');
      codeInput.value = '';
      setTimeout(loadStatus, 8000);
      startPolling();
    }
  } catch (error) {
    showMessage(error?.message || '提交验证码失败', 'error');
  } finally {
    submitting.value = false;
  }
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(loadStatus, 10000);
  setTimeout(stopPolling, 180000);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

onMounted(() => {
  loadStatus();
  startPolling();
});
onUnmounted(stopPolling);

return (_ctx, _cache) => {
  const _component_VIcon = _resolveComponent("VIcon");
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VToolbar = _resolveComponent("VToolbar");
  const _component_VDivider = _resolveComponent("VDivider");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VCardTitle = _resolveComponent("VCardTitle");
  const _component_VTextField = _resolveComponent("VTextField");
  const _component_VCardText = _resolveComponent("VCardText");
  const _component_VCard = _resolveComponent("VCard");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VRow = _resolveComponent("VRow");
  const _component_VChip = _resolveComponent("VChip");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VToolbar, {
      density: "comfortable",
      color: "transparent",
      class: "px-0"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VIcon, {
          icon: "mdi-account-key",
          color: "primary",
          class: "me-2"
        }),
        _cache[5] || (_cache[5] = _createElementVNode("div", { class: "text-h6" }, "馒头自动登录保活", -1)),
        _createVNode(_component_VSpacer),
        _createVNode(_component_VBtn, {
          color: "primary",
          variant: "tonal",
          loading: triggering.value,
          class: "me-2",
          onClick: loginNow
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VIcon, {
              icon: "mdi-login",
              class: "me-1"
            }),
            _cache[3] || (_cache[3] = _createTextVNode("立即登录 ", -1))
          ]),
          _: 1
        }, 8, ["loading"]),
        _createVNode(_component_VBtn, {
          color: "warning",
          variant: "tonal",
          loading: triggering.value,
          class: "me-2",
          onClick: reverify
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VIcon, {
              icon: "mdi-shield-refresh",
              class: "me-1"
            }),
            _cache[4] || (_cache[4] = _createTextVNode("重新验证 ", -1))
          ]),
          _: 1
        }, 8, ["loading"]),
        _createVNode(_component_VBtn, {
          icon: "mdi-refresh",
          variant: "text",
          loading: loading.value,
          title: "刷新状态",
          onClick: loadStatus
        }, null, 8, ["loading"]),
        _createVNode(_component_VBtn, {
          icon: "mdi-close",
          variant: "text",
          title: "关闭",
          onClick: _cache[0] || (_cache[0] = $event => (emit('close')))
        })
      ]),
      _: 1
    }),
    _createVNode(_component_VDivider, { class: "mb-4" }),
    (message.text)
      ? (_openBlock(), _createBlock(_component_VAlert, {
          key: 0,
          type: message.type,
          variant: "tonal",
          density: "compact",
          class: "mb-4"
        }, {
          default: _withCtx(() => [
            _createTextVNode(_toDisplayString(message.text), 1)
          ]),
          _: 1
        }, 8, ["type"]))
      : _createCommentVNode("", true),
    (!status.enabled)
      ? (_openBlock(), _createBlock(_component_VAlert, {
          key: 1,
          type: "warning",
          variant: "tonal",
          density: "compact",
          class: "mb-4"
        }, {
          default: _withCtx(() => [...(_cache[6] || (_cache[6] = [
            _createTextVNode(" 插件未启用，请在「配置」中启用并填写用户名与密码。 ", -1)
          ]))]),
          _: 1
        }))
      : (!status.has_password)
        ? (_openBlock(), _createBlock(_component_VAlert, {
            key: 2,
            type: "error",
            variant: "tonal",
            density: "compact",
            class: "mb-4"
          }, {
            default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
              _createTextVNode(" 未检测到密码，请先在「配置」中补全凭据。 ", -1)
            ]))]),
            _: 1
          }))
        : _createCommentVNode("", true),
    (status.enabled && status.has_password && !status.has_totp)
      ? (_openBlock(), _createBlock(_component_VAlert, {
          key: 3,
          type: "info",
          variant: "tonal",
          density: "compact",
          class: "mb-4"
        }, {
          default: _withCtx(() => [
            _createElementVNode("div", _hoisted_2, [
              _createVNode(_component_VIcon, { icon: "mdi-shield-key-outline" }),
              _cache[8] || (_cache[8] = _createElementVNode("span", { class: "flex-grow-1" }, " 当前使用「邮箱验证码」：验证到期时需要你手动填一次码（约 30 天一次）。 填入 OTP 密钥后可改为全自动，永不再打扰。 ", -1)),
              _createVNode(_component_VBtn, {
                size: "small",
                variant: "tonal",
                color: "primary",
                onClick: _cache[1] || (_cache[1] = $event => (showTotpGuide.value = !showTotpGuide.value))
              }, {
                default: _withCtx(() => [
                  _createTextVNode(_toDisplayString(showTotpGuide.value ? '收起' : '如何开启'), 1)
                ]),
                _: 1
              })
            ]),
            (showTotpGuide.value)
              ? (_openBlock(), _createElementBlock("ol", _hoisted_3, [...(_cache[9] || (_cache[9] = [
                  _createElementVNode("li", null, "浏览器登录馒头网页 → 控制台 → 安全設定 → 二級驗證。", -1),
                  _createElementVNode("li", null, "启用 OTP，复制二维码下方那段 Base32 密钥。", -1),
                  _createElementVNode("li", null, "到本插件「配置」页填进「OTP 验证器密钥」并保存。", -1),
                  _createElementVNode("li", null, "此后验证码由插件自动计算提交，不再需要人工介入。", -1)
                ]))]))
              : _createCommentVNode("", true)
          ]),
          _: 1
        }))
      : _createCommentVNode("", true),
    (status.awaiting_code)
      ? (_openBlock(), _createBlock(_component_VCard, {
          key: 4,
          variant: "outlined",
          class: "mb-4",
          border: "",
          color: "warning"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VCardTitle, { class: "text-subtitle-1" }, {
              default: _withCtx(() => [
                _createVNode(_component_VIcon, {
                  icon: "mdi-email-fast",
                  color: "warning",
                  class: "me-2"
                }),
                _cache[10] || (_cache[10] = _createTextVNode("需要填写邮箱验证码 ", -1))
              ]),
              _: 1
            }),
            _createVNode(_component_VCardText, null, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_4, [
                  _cache[11] || (_cache[11] = _createTextVNode(" 插件已自动点「获取验证码」，请到 ", -1)),
                  _createElementVNode("strong", null, _toDisplayString(status.email || '注册邮箱'), 1),
                  _createTextVNode(" 查收（含垃圾邮件箱）。请求时间 " + _toDisplayString(status.code_requested_at || '-') + "， 本次等待截止 " + _toDisplayString(status.code_deadline || '-') + "。 ", 1)
                ]),
                _createElementVNode("div", _hoisted_5, [
                  _createVNode(_component_VTextField, {
                    modelValue: codeInput.value,
                    "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((codeInput).value = $event)),
                    label: "6 位邮箱验证码",
                    placeholder: "填入邮件中的验证码",
                    variant: "outlined",
                    density: "compact",
                    "hide-details": "",
                    style: {"max-width":"240px"},
                    onKeyup: _withKeys(submitCode, ["enter"])
                  }, null, 8, ["modelValue"]),
                  _createVNode(_component_VBtn, {
                    color: "warning",
                    loading: submitting.value,
                    onClick: submitCode
                  }, {
                    default: _withCtx(() => [...(_cache[12] || (_cache[12] = [
                      _createTextVNode("提交验证码", -1)
                    ]))]),
                    _: 1
                  }, 8, ["loading"])
                ]),
                _createElementVNode("div", _hoisted_6, " 不方便现在填？直接关掉即可。插件会在 " + _toDisplayString(status.retry_interval) + " 分钟后自动重新发码， 每天最多 " + _toDisplayString(status.retry_times) + " 次；你也可以随时点右上「立即登录」重新发码， 40 天保活期内任何方便的时候补上都来得及。 ", 1)
              ]),
              _: 1
            })
          ]),
          _: 1
        }))
      : _createCommentVNode("", true),
    _createVNode(_component_VRow, { dense: "" }, {
      default: _withCtx(() => [
        _createVNode(_component_VCol, {
          cols: "12",
          md: "3"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VCard, { variant: "outlined" }, {
              default: _withCtx(() => [
                _createVNode(_component_VCardText, null, {
                  default: _withCtx(() => [
                    _cache[13] || (_cache[13] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "执行周期", -1)),
                    _createElementVNode("div", _hoisted_7, _toDisplayString(status.cron || '-'), 1),
                    _createElementVNode("div", _hoisted_8, "下次 " + _toDisplayString(status.next_run || '未排期'), 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "3"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VCard, { variant: "outlined" }, {
              default: _withCtx(() => [
                _createVNode(_component_VCardText, null, {
                  default: _withCtx(() => [
                    _cache[14] || (_cache[14] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "最近结果", -1)),
                    _createElementVNode("div", {
                      class: _normalizeClass(["text-h6", `text-${statusColor.value}`])
                    }, _toDisplayString(status.last_result ? (lastSuccess.value ? '成功' : '失败') : '尚未执行'), 3),
                    _createElementVNode("div", _hoisted_9, _toDisplayString(status.last_result?.at || '-'), 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "3"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VCard, { variant: "outlined" }, {
              default: _withCtx(() => [
                _createVNode(_component_VCardText, null, {
                  default: _withCtx(() => [
                    _cache[15] || (_cache[15] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "设备受信剩余", -1)),
                    _createElementVNode("div", {
                      class: _normalizeClass(["text-h6", `text-${deviceColor.value}`])
                    }, _toDisplayString(deviceExpire.value === null || deviceExpire.value === undefined ? '待确认' : `${deviceExpire.value} 天`), 3),
                    _createElementVNode("div", _hoisted_10, " 已验证 " + _toDisplayString(status.device_verified_at || '未记录') + " / 共 " + _toDisplayString(status.device_valid_days) + " 天 ", 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "3"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VCard, { variant: "outlined" }, {
              default: _withCtx(() => [
                _createVNode(_component_VCardText, null, {
                  default: _withCtx(() => [
                    _createElementVNode("div", _hoisted_11, "距 " + _toDisplayString(status.keepalive_days) + " 天保活线", 1),
                    _createElementVNode("div", _hoisted_12, _toDisplayString(remaining.value === null || remaining.value === undefined ? '待复核' : `${remaining.value} 天`), 1),
                    _createElementVNode("div", _hoisted_13, "站点最近浏览 " + _toDisplayString(status.last_result?.last_browse || '-'), 1)
                  ]),
                  _: 1
                })
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createVNode(_component_VCard, {
      variant: "outlined",
      class: "mt-4"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCardTitle, { class: "text-subtitle-1" }, {
          default: _withCtx(() => [...(_cache[16] || (_cache[16] = [
            _createTextVNode("最近一次执行", -1)
          ]))]),
          _: 1
        }),
        (status.last_result)
          ? (_openBlock(), _createBlock(_component_VCardText, { key: 0 }, {
              default: _withCtx(() => [
                _createElementVNode("div", _hoisted_14, "执行时间：" + _toDisplayString(status.last_result.at || '-') + "（耗时 " + _toDisplayString(status.last_result.seconds ?? '-') + " 秒）", 1),
                _createElementVNode("div", _hoisted_15, "结果：" + _toDisplayString(status.last_result.message || '-'), 1),
                (status.last_result.verify)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_16, "站点复核：" + _toDisplayString(status.last_result.verify), 1))
                  : _createCommentVNode("", true),
                _createElementVNode("div", _hoisted_17, " 账号：" + _toDisplayString(status.username || '-') + " · 邮箱：" + _toDisplayString(status.email || '未填') + " · 验证方式：" + _toDisplayString(status.has_totp ? 'OTP 自动（无需人工）' : '邮箱验证码（到期需手动填）') + " · 代理：" + _toDisplayString(status.use_proxy ? '走系统代理' : '直连'), 1),
                (status.last_result.screenshot)
                  ? (_openBlock(), _createBlock(_component_VAlert, {
                      key: 1,
                      type: "info",
                      variant: "tonal",
                      density: "compact",
                      class: "mt-3"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(" 现场截图已保存为插件数据目录下的 " + _toDisplayString(status.last_result.screenshot) + "，可下载排查。 ", 1)
                      ]),
                      _: 1
                    }))
                  : _createCommentVNode("", true)
              ]),
              _: 1
            }))
          : (_openBlock(), _createBlock(_component_VCardText, {
              key: 1,
              class: "text-caption text-medium-emphasis"
            }, {
              default: _withCtx(() => [...(_cache[17] || (_cache[17] = [
                _createTextVNode("尚未执行过登录", -1)
              ]))]),
              _: 1
            }))
      ]),
      _: 1
    }),
    _createVNode(_component_VCard, {
      variant: "outlined",
      class: "mt-4"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCardTitle, { class: "text-subtitle-1" }, {
          default: _withCtx(() => [...(_cache[18] || (_cache[18] = [
            _createTextVNode("登录历史", -1)
          ]))]),
          _: 1
        }),
        (status.history?.length)
          ? (_openBlock(), _createBlock(_component_VCardText, { key: 0 }, {
              default: _withCtx(() => [
                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(status.history, (item, i) => {
                  return (_openBlock(), _createElementBlock("div", {
                    key: i,
                    class: "d-flex align-start py-2",
                    style: {"border-bottom":"1px solid rgba(128,128,128,0.16)"}
                  }, [
                    _createVNode(_component_VIcon, {
                      icon: item.success ? 'mdi-check-circle' : 'mdi-alert-circle',
                      color: item.success ? 'success' : 'error',
                      size: "small",
                      class: "me-2 mt-1"
                    }, null, 8, ["icon", "color"]),
                    _createElementVNode("div", _hoisted_18, [
                      _createElementVNode("div", _hoisted_19, [
                        _createTextVNode(_toDisplayString(item.at || '-'), 1),
                        (item.mode)
                          ? (_openBlock(), _createElementBlock("span", _hoisted_20, " · " + _toDisplayString(item.mode), 1))
                          : _createCommentVNode("", true)
                      ]),
                      _createElementVNode("div", _hoisted_21, _toDisplayString(item.message || '-'), 1),
                      (item.verify)
                        ? (_openBlock(), _createElementBlock("div", _hoisted_22, _toDisplayString(item.verify), 1))
                        : _createCommentVNode("", true)
                    ]),
                    (item.remaining !== null && item.remaining !== undefined)
                      ? (_openBlock(), _createBlock(_component_VChip, {
                          key: 0,
                          size: "small",
                          variant: "tonal",
                          color: "primary"
                        }, {
                          default: _withCtx(() => [
                            _createTextVNode(" 剩 " + _toDisplayString(item.remaining) + " 天 ", 1)
                          ]),
                          _: 2
                        }, 1024))
                      : _createCommentVNode("", true)
                  ]))
                }), 128))
              ]),
              _: 1
            }))
          : (_openBlock(), _createBlock(_component_VCardText, {
              key: 1,
              class: "text-caption text-medium-emphasis"
            }, {
              default: _withCtx(() => [...(_cache[19] || (_cache[19] = [
                _createTextVNode("暂无历史记录", -1)
              ]))]),
              _: 1
            }))
      ]),
      _: 1
    })
  ]))
}
}

};

export { _sfc_main as default };
