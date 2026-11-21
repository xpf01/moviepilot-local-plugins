import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "pa-4" };

const {onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'MTeamAutoLogin' },
  initialConfig: { type: Object, default: () => ({}) },
},
  emits: ['save', 'close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const saving = ref(false);
const showPassword = ref(false);
const message = reactive({ text: '', type: 'info' });

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
};

const config = reactive({ ...defaults });

function showMessage(text, type = 'info') {
  message.text = text;
  message.type = type;
  if (text) setTimeout(() => { if (message.text === text) message.text = ''; }, 3500);
}

async function saveConfig() {
  if (typeof props.api?.put !== 'function') {
    showMessage('当前 MoviePilot 未提供配置保存接口', 'error');
    return
  }
  if (config.enabled && (!config.username || !config.password)) {
    showMessage('启用前请先填写馒头用户名与密码', 'error');
    return
  }
  const totp = String(config.totp_secret || '').replace(/[\s-]/g, '').toUpperCase();
  if (totp && !/^[A-Z2-7]+=*$/.test(totp)) {
    showMessage('OTP 密钥格式不对：只允许字母 A-Z 和数字 2-7，请从二维码下方的纯文本复制', 'error');
    return
  }
  if (totp && totp.replace(/=+$/, '').length < 16) {
    showMessage('OTP 密钥长度偏短（常见 16 或 32 位），请确认是否复制完整', 'error');
    return
  }
  saving.value = true;
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
    };
    const response = await props.api.put(`plugin/${props.pluginId || 'MTeamAutoLogin'}`, payload);
    const result = response?.data ?? response;
    if (result?.success === false) throw new Error(result.message || '保存配置失败')
    emit('save', payload);
    showMessage('配置已保存', 'success');
  } catch (error) {
    showMessage(error?.message || '保存配置失败', 'error');
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  const incoming = props.initialConfig || {};
  Object.assign(config, defaults);
  for (const key of Object.keys(defaults)) {
    if (incoming[key] !== undefined && incoming[key] !== null) config[key] = incoming[key];
  }
});

return (_ctx, _cache) => {
  const _component_VIcon = _resolveComponent("VIcon");
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VToolbar = _resolveComponent("VToolbar");
  const _component_VDivider = _resolveComponent("VDivider");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VSwitch = _resolveComponent("VSwitch");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VRow = _resolveComponent("VRow");
  const _component_VTextField = _resolveComponent("VTextField");
  const _component_VCardTitle = _resolveComponent("VCardTitle");
  const _component_VExpansionPanelTitle = _resolveComponent("VExpansionPanelTitle");
  const _component_VExpansionPanelText = _resolveComponent("VExpansionPanelText");
  const _component_VExpansionPanel = _resolveComponent("VExpansionPanel");
  const _component_VExpansionPanels = _resolveComponent("VExpansionPanels");
  const _component_VCardText = _resolveComponent("VCardText");
  const _component_VCard = _resolveComponent("VCard");

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
        _cache[16] || (_cache[16] = _createElementVNode("div", { class: "text-h6" }, "馒头自动登录保活配置", -1)),
        _createVNode(_component_VSpacer),
        _createVNode(_component_VBtn, {
          icon: "mdi-content-save",
          variant: "text",
          color: "success",
          loading: saving.value,
          title: "保存配置",
          onClick: saveConfig
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
    _createVNode(_component_VAlert, {
      type: "info",
      variant: "tonal",
      density: "compact",
      class: "mb-4"
    }, {
      default: _withCtx(() => [...(_cache[17] || (_cache[17] = [
        _createTextVNode(" 馒头 40 天保活只认「用浏览器存取网页」，API 访问和做种都不算。插件每天用真实浏览器存取一次； 站点强制登入验证码且每台设备 30 天有效，因此浏览器使用持久化身份。 填了 OTP 密钥后验证全自动、永不打扰；不填则到期时自动发邮箱验证码并通知你手动填一次。 ", -1)
      ]))]),
      _: 1
    }),
    _createVNode(_component_VRow, { dense: "" }, {
      default: _withCtx(() => [
        _createVNode(_component_VCol, {
          cols: "12",
          md: "3"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VSwitch, {
              modelValue: config.enabled,
              "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((config.enabled) = $event)),
              label: "启用插件",
              color: "success",
              "hide-details": ""
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "3"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VSwitch, {
              modelValue: config.notify_success,
              "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.notify_success) = $event)),
              label: "成功也通知",
              color: "primary",
              "hide-details": ""
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "3"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VSwitch, {
              modelValue: config.use_proxy,
              "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.use_proxy) = $event)),
              label: "浏览器走系统代理",
              color: "info",
              "hide-details": ""
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "3"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VSwitch, {
              modelValue: config.onlyonce,
              "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.onlyonce) = $event)),
              label: "保存后立即登录一次",
              color: "warning",
              "hide-details": ""
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createVNode(_component_VRow, {
      dense: "",
      class: "mt-4"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCol, {
          cols: "12",
          md: "6"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VTextField, {
              modelValue: config.email,
              "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.email) = $event)),
              label: "注册邮箱（验证码发到这个邮箱）",
              placeholder: "与馒头账号绑定的 Gmail",
              variant: "outlined",
              density: "compact",
              color: "primary",
              "hide-details": "",
              "persistent-hint": "",
              hint: "必填。验证到期时插件用它在登录页点「获取验证码」"
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "6"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VTextField, {
              modelValue: config.username,
              "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.username) = $event)),
              label: "馒头用户名",
              placeholder: "登录用户名",
              variant: "outlined",
              density: "compact",
              autocomplete: "off",
              "hide-details": ""
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "6"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VTextField, {
              modelValue: config.password,
              "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((config.password) = $event)),
              label: "馒头密码",
              type: showPassword.value ? 'text' : 'password',
              "append-inner-icon": showPassword.value ? 'mdi-eye-off' : 'mdi-eye',
              variant: "outlined",
              density: "compact",
              autocomplete: "new-password",
              "hide-details": "",
              "onClick:appendInner": _cache[8] || (_cache[8] = $event => (showPassword.value = !showPassword.value))
            }, null, 8, ["modelValue", "type", "append-inner-icon"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "6"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VTextField, {
              modelValue: config.cron,
              "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((config.cron) = $event)),
              label: "执行周期（5 位 cron）",
              placeholder: "17 8 * * *",
              variant: "outlined",
              density: "compact",
              "hide-details": "",
              "persistent-hint": "",
              hint: "默认每天 08:17 存取一次"
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "6"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VTextField, {
              modelValue: config.home_url,
              "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((config.home_url) = $event)),
              label: "站点首页地址",
              placeholder: "https://kp.m-team.cc/",
              variant: "outlined",
              density: "compact",
              "hide-details": "",
              "persistent-hint": "",
              hint: "日常保活直接存取这个页面"
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "6"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VTextField, {
              modelValue: config.login_url,
              "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((config.login_url) = $event)),
              label: "登录页地址",
              placeholder: "https://kp.m-team.cc/login",
              variant: "outlined",
              density: "compact",
              "hide-details": "",
              "persistent-hint": "",
              hint: "站点换域名时改这里"
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createVNode(_component_VRow, {
      dense: "",
      class: "mt-4"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCol, {
          cols: "12",
          md: "4"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VTextField, {
              modelValue: config.code_wait,
              "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((config.code_wait) = $event)),
              modelModifiers: { number: true },
              type: "number",
              label: "等待填入验证码（秒）",
              variant: "outlined",
              density: "compact",
              "hide-details": "",
              "persistent-hint": "",
              hint: "默认 600 秒，过期按重试策略再来"
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "4"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VTextField, {
              modelValue: config.retry_interval,
              "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => ((config.retry_interval) = $event)),
              modelModifiers: { number: true },
              type: "number",
              label: "补码重试间隔（分钟）",
              variant: "outlined",
              density: "compact",
              "hide-details": "",
              "persistent-hint": "",
              hint: "默认 20 分钟，每次重试会重新发码"
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "4"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VTextField, {
              modelValue: config.retry_times,
              "onUpdate:modelValue": _cache[14] || (_cache[14] = $event => ((config.retry_times) = $event)),
              modelModifiers: { number: true },
              type: "number",
              label: "每日补码重试次数",
              variant: "outlined",
              density: "compact",
              "hide-details": "",
              "persistent-hint": "",
              hint: "默认 3 次，填 0 表示不自动重试"
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, { cols: "12" }, {
          default: _withCtx(() => [
            _createVNode(_component_VCard, {
              variant: "outlined",
              color: "primary"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_VCardTitle, { class: "text-subtitle-1 d-flex align-center" }, {
                  default: _withCtx(() => [
                    _createVNode(_component_VIcon, {
                      icon: "mdi-shield-key",
                      class: "me-2"
                    }),
                    _cache[18] || (_cache[18] = _createTextVNode("验证方式选择（决定要不要你手动填码） ", -1))
                  ]),
                  _: 1
                }),
                _createVNode(_component_VCardText, null, {
                  default: _withCtx(() => [
                    _createVNode(_component_VAlert, {
                      type: "info",
                      variant: "tonal",
                      density: "compact",
                      class: "mb-3"
                    }, {
                      default: _withCtx(() => [...(_cache[19] || (_cache[19] = [
                        _createTextVNode(" 馒头支持三种登录验证：", -1),
                        _createElementVNode("strong", null, "邮箱验证码", -1),
                        _createTextVNode("、", -1),
                        _createElementVNode("strong", null, "OTP 验证器", -1),
                        _createTextVNode("、Telegram Bot。 填了下面的密钥就自动走 OTP，插件自己算码提交，", -1),
                        _createElementVNode("strong", null, "永远不需要你手动填", -1),
                        _createTextVNode("。 不填则走邮箱验证码，验证到期时要你手动填一次（约 30 天一次）。 ", -1)
                      ]))]),
                      _: 1
                    }),
                    _createVNode(_component_VTextField, {
                      modelValue: config.totp_secret,
                      "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => ((config.totp_secret) = $event)),
                      label: "OTP 验证器密钥（Base32，强烈建议填写）",
                      placeholder: "例如 JBSWY3DPEHPK3PXP",
                      variant: "outlined",
                      density: "compact",
                      color: "primary",
                      "hide-details": "",
                      "persistent-hint": "",
                      hint: "填了它就不再需要邮箱验证码，也不会再打扰你"
                    }, null, 8, ["modelValue"]),
                    _createVNode(_component_VExpansionPanels, {
                      variant: "accordion",
                      class: "mt-3"
                    }, {
                      default: _withCtx(() => [
                        _createVNode(_component_VExpansionPanel, null, {
                          default: _withCtx(() => [
                            _createVNode(_component_VExpansionPanelTitle, { class: "text-body-2" }, {
                              default: _withCtx(() => [...(_cache[20] || (_cache[20] = [
                                _createTextVNode("怎么获取这个密钥？点开看步骤", -1)
                              ]))]),
                              _: 1
                            }),
                            _createVNode(_component_VExpansionPanelText, null, {
                              default: _withCtx(() => [
                                _cache[23] || (_cache[23] = _createElementVNode("ol", {
                                  class: "text-body-2 ps-5",
                                  style: {"line-height":"1.9"}
                                }, [
                                  _createElementVNode("li", null, "浏览器登录馒头网页，进入「控制台 → 安全設定 → 二級驗證」。"),
                                  _createElementVNode("li", null, [
                                    _createTextVNode("启用 OTP 二级验证，页面会显示二维码和一段 "),
                                    _createElementVNode("strong", null, "Base32 密钥"),
                                    _createTextVNode("（形如 JBSWY3DPEHPK3PXP）。")
                                  ]),
                                  _createElementVNode("li", null, "把这段密钥复制到上面的输入框，点保存。"),
                                  _createElementVNode("li", null, "二维码下方「无法扫描？」一类链接通常会直接显示纯文本密钥；只认字母 A-Z 和数字 2-7。")
                                ], -1)),
                                _createVNode(_component_VAlert, {
                                  type: "warning",
                                  variant: "tonal",
                                  density: "compact",
                                  class: "mt-2"
                                }, {
                                  default: _withCtx(() => [...(_cache[21] || (_cache[21] = [
                                    _createTextVNode(" 手机上的验证器 App 不用非得绑定，插件本身就是验证器。但建议同时用 App 扫一次二维码做备份， 以免日后换设备时拿不到密钥。 ", -1)
                                  ]))]),
                                  _: 1
                                }),
                                _createVNode(_component_VAlert, {
                                  type: "info",
                                  variant: "tonal",
                                  density: "compact",
                                  class: "mt-2"
                                }, {
                                  default: _withCtx(() => [...(_cache[22] || (_cache[22] = [
                                    _createTextVNode(" 站点官方说明：若遗失 OTP 二级验证，仍可用「密码 + 邮箱验证」登录， 再到控制台自行关闭，不会因此锁死账号。 ", -1)
                                  ]))]),
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
                    })
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
    _createVNode(_component_VAlert, {
      type: "warning",
      variant: "tonal",
      density: "compact",
      class: "mt-4"
    }, {
      default: _withCtx(() => [...(_cache[24] || (_cache[24] = [
        _createTextVNode(" 不需要填邮箱密码或 IMAP 授权码：插件只在登录页点「获取验证码」，验证码由你从邮箱看到后手动填入插件页面。 ", -1)
      ]))]),
      _: 1
    })
  ]))
}
}

};

export { _sfc_main as default };
