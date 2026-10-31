import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,Fragment:_Fragment,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "pa-4" };
const _hoisted_2 = { class: "text-h5" };
const _hoisted_3 = { class: "text-subtitle-2" };
const _hoisted_4 = { class: "text-h5" };
const _hoisted_5 = { class: "text-subtitle-2" };
const _hoisted_6 = { class: "text-h5" };
const _hoisted_7 = { class: "text-subtitle-2" };
const _hoisted_8 = { class: "text-h5" };
const _hoisted_9 = { class: "text-subtitle-2" };
const _hoisted_10 = { class: "text-body-2" };
const _hoisted_11 = { class: "d-flex flex-wrap justify-end mt-4 ga-2" };

const {onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'DeepSeekBalanceMonitor' },
},
  emits: ['close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const loading = ref(false);
const running = ref(false);
const message = reactive({ text: '', type: 'info' });
const status = reactive({
  enabled: false,
  alerted: false,
  threshold: 5.0,
  last_report: '',
  balance: {},
  top_up_url: 'https://platform.deepseek.com/top_up',
  usage_url: 'https://platform.deepseek.com/usage',
});

function showMessage(text, type = 'info') {
  message.text = text;
  message.type = type;
  if (text) setTimeout(() => { if (message.text === text) message.text = ''; }, 4000);
}

function fmt(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return '—'
  return n.toFixed(4)
}

async function loadStatus() {
  loading.value = true;
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'DeepSeekBalanceMonitor'}/status`);
    const result = response?.data ?? response;
    if (result?.success !== false) {
      Object.assign(status, result?.data ?? result ?? {});
    }
  } catch (error) {
    /* 忽略状态读取失败 */
  } finally {
    loading.value = false;
  }
}

async function checkNow() {
  running.value = true;
  try {
    const response = await props.api.post(`plugin/${props.pluginId || 'DeepSeekBalanceMonitor'}/check_now`, {});
    const result = response?.data ?? response;
    if (result?.success === false) throw new Error(result.message || '检查失败')
    await loadStatus();
    showMessage('检查完成', 'success');
  } catch (error) {
    showMessage(error?.message || '检查失败', 'error');
  } finally {
    running.value = false;
  }
}

function openUrl(url) {
  if (url) window.open(url, '_blank');
}

onMounted(loadStatus);

return (_ctx, _cache) => {
  const _component_VIcon = _resolveComponent("VIcon");
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VToolbar = _resolveComponent("VToolbar");
  const _component_VDivider = _resolveComponent("VDivider");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VCardText = _resolveComponent("VCardText");
  const _component_VCard = _resolveComponent("VCard");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VRow = _resolveComponent("VRow");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VToolbar, {
      density: "comfortable",
      color: "transparent",
      class: "px-0"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VIcon, {
          icon: "mdi-currency-cny",
          color: "primary",
          class: "me-2"
        }),
        _cache[3] || (_cache[3] = _createElementVNode("div", { class: "text-h6" }, "DeepSeek余额监控", -1)),
        _createVNode(_component_VSpacer),
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
          default: _withCtx(() => [...(_cache[4] || (_cache[4] = [
            _createTextVNode(" 插件未启用，请在「配置」中启用。 ", -1)
          ]))]),
          _: 1
        }))
      : (_openBlock(), _createElementBlock(_Fragment, { key: 2 }, [
          _createVNode(_component_VAlert, {
            type: status.alerted ? 'warning' : 'success',
            variant: "tonal",
            density: "compact",
            class: "mb-4"
          }, {
            default: _withCtx(() => [
              _createTextVNode(" 告警状态：" + _toDisplayString(status.alerted ? '已告警（欠费或低于阈值）' : '正常'), 1)
            ]),
            _: 1
          }, 8, ["type"]),
          _createVNode(_component_VRow, { dense: "" }, {
            default: _withCtx(() => [
              _createVNode(_component_VCol, {
                cols: "12",
                md: "3"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_VCard, {
                    variant: "outlined",
                    class: "text-center"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VCardText, null, {
                        default: _withCtx(() => [
                          _cache[5] || (_cache[5] = _createElementVNode("div", { class: "text-caption text-grey" }, "总可用余额", -1)),
                          _createElementVNode("div", _hoisted_2, [
                            _createTextVNode(_toDisplayString(fmt(status.balance?.total_balance)) + " ", 1),
                            _createElementVNode("span", _hoisted_3, _toDisplayString(status.balance?.currency || ''), 1)
                          ])
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
                  _createVNode(_component_VCard, {
                    variant: "outlined",
                    class: "text-center"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VCardText, null, {
                        default: _withCtx(() => [
                          _cache[6] || (_cache[6] = _createElementVNode("div", { class: "text-caption text-grey" }, "充值余额", -1)),
                          _createElementVNode("div", _hoisted_4, [
                            _createTextVNode(_toDisplayString(fmt(status.balance?.topped_up_balance)) + " ", 1),
                            _createElementVNode("span", _hoisted_5, _toDisplayString(status.balance?.currency || ''), 1)
                          ])
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
                  _createVNode(_component_VCard, {
                    variant: "outlined",
                    class: "text-center"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VCardText, null, {
                        default: _withCtx(() => [
                          _cache[7] || (_cache[7] = _createElementVNode("div", { class: "text-caption text-grey" }, "赠金", -1)),
                          _createElementVNode("div", _hoisted_6, [
                            _createTextVNode(_toDisplayString(fmt(status.balance?.granted_balance)) + " ", 1),
                            _createElementVNode("span", _hoisted_7, _toDisplayString(status.balance?.currency || ''), 1)
                          ])
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
                  _createVNode(_component_VCard, {
                    variant: "outlined",
                    class: "text-center"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VCardText, null, {
                        default: _withCtx(() => [
                          _cache[8] || (_cache[8] = _createElementVNode("div", { class: "text-caption text-grey" }, "告警阈值", -1)),
                          _createElementVNode("div", _hoisted_8, [
                            _createTextVNode(_toDisplayString(fmt(status.threshold)) + " ", 1),
                            _createElementVNode("span", _hoisted_9, _toDisplayString(status.balance?.currency || ''), 1)
                          ])
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
            class: "mt-3"
          }, {
            default: _withCtx(() => [
              _createVNode(_component_VCardText, null, {
                default: _withCtx(() => [
                  _cache[9] || (_cache[9] = _createElementVNode("div", { class: "text-subtitle-2 mb-1" }, "最近余额报告", -1)),
                  _createElementVNode("div", _hoisted_10, _toDisplayString(status.last_report || '尚未执行检查'), 1)
                ]),
                _: 1
              })
            ]),
            _: 1
          }),
          _createVNode(_component_VAlert, {
            type: "info",
            variant: "tonal",
            density: "compact",
            class: "mt-3 mb-0"
          }, {
            default: _withCtx(() => [...(_cache[10] || (_cache[10] = [
              _createTextVNode(" 消费金额、API 请求次数、Token 用量官方未提供 API，请在用量看板中查看。 ", -1)
            ]))]),
            _: 1
          }),
          _createElementVNode("div", _hoisted_11, [
            _createVNode(_component_VBtn, {
              color: "primary",
              "prepend-icon": "mdi-play",
              loading: running.value,
              onClick: checkNow
            }, {
              default: _withCtx(() => [...(_cache[11] || (_cache[11] = [
                _createTextVNode("立即检查", -1)
              ]))]),
              _: 1
            }, 8, ["loading"]),
            _createVNode(_component_VBtn, {
              color: "secondary",
              "prepend-icon": "mdi-chart-box",
              onClick: _cache[1] || (_cache[1] = $event => (openUrl(status.usage_url)))
            }, {
              default: _withCtx(() => [...(_cache[12] || (_cache[12] = [
                _createTextVNode("用量看板", -1)
              ]))]),
              _: 1
            }),
            _createVNode(_component_VBtn, {
              color: "success",
              "prepend-icon": "mdi-cash-plus",
              onClick: _cache[2] || (_cache[2] = $event => (openUrl(status.top_up_url)))
            }, {
              default: _withCtx(() => [...(_cache[13] || (_cache[13] = [
                _createTextVNode("前往充值", -1)
              ]))]),
              _: 1
            })
          ])
        ], 64))
  ]))
}
}

};

export { _sfc_main as default };
