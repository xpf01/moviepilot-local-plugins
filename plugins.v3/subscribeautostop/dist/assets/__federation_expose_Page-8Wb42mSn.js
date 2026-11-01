import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,createTextVNode:_createTextVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "pa-4" };
const _hoisted_2 = { class: "text-h6" };
const _hoisted_3 = { class: "text-h6" };
const _hoisted_4 = { class: "text-h6" };
const _hoisted_5 = { class: "text-h6" };
const _hoisted_6 = { class: "text-body-2 mb-2" };
const _hoisted_7 = { key: 0 };
const _hoisted_8 = { class: "flex-grow-1" };
const _hoisted_9 = {
  key: 0,
  class: "text-caption text-medium-emphasis"
};
const _hoisted_10 = {
  key: 1,
  class: "text-caption text-medium-emphasis"
};

const {onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'SubscribeAutoStop' },
},
  emits: ['close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const loading = ref(false);
const scanning = ref(false);
const message = reactive({ text: '', type: 'info' });
const status = reactive({ enabled: false, cron: '', action: 'pause', notify: false, last_report: null });

function showMessage(text, type = 'info') {
  message.text = text;
  message.type = type;
  if (text) setTimeout(() => { if (message.text === text) message.text = ''; }, 4000);
}

async function loadStatus() {
  loading.value = true;
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'SubscribeAutoStop'}/status`);
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

async function scanNow() {
  scanning.value = true;
  try {
    const response = await props.api.post(`plugin/${props.pluginId || 'SubscribeAutoStop'}/scan`, {});
    const result = response?.data ?? response;
    if (result?.success === false) {
      showMessage(result?.message || '扫描失败', 'error');
    } else {
      if (result?.data) status.last_report = result.data;
      showMessage('扫描完成', 'success');
    }
  } catch (error) {
    showMessage(error?.message || '扫描失败', 'error');
  } finally {
    scanning.value = false;
  }
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
  const _component_VCardTitle = _resolveComponent("VCardTitle");
  const _component_VChip = _resolveComponent("VChip");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VToolbar, {
      density: "comfortable",
      color: "transparent",
      class: "px-0"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VIcon, {
          icon: "mdi-auto-download",
          color: "primary",
          class: "me-2"
        }),
        _cache[2] || (_cache[2] = _createElementVNode("div", { class: "text-h6" }, "订阅入库自停", -1)),
        _createVNode(_component_VSpacer),
        _createVNode(_component_VBtn, {
          color: "primary",
          loading: scanning.value,
          onClick: scanNow,
          class: "me-2"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VIcon, {
              icon: "mdi-play",
              class: "me-1"
            }),
            _cache[1] || (_cache[1] = _createTextVNode("立即扫描 ", -1))
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
          default: _withCtx(() => [...(_cache[3] || (_cache[3] = [
            _createTextVNode(" 插件未启用，请在「配置」中启用。 ", -1)
          ]))]),
          _: 1
        }))
      : (_openBlock(), _createElementBlock(_Fragment, { key: 2 }, [
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
                          _cache[4] || (_cache[4] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "定时表达式", -1)),
                          _createElementVNode("div", _hoisted_2, _toDisplayString(status.cron), 1)
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
                          _cache[5] || (_cache[5] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "命中动作", -1)),
                          _createElementVNode("div", _hoisted_3, _toDisplayString(status.action === 'delete' ? '删除订阅' : '暂停订阅'), 1)
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
                          _cache[6] || (_cache[6] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "通知", -1)),
                          _createElementVNode("div", _hoisted_4, _toDisplayString(status.notify ? '开启' : '关闭'), 1)
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
                          _cache[7] || (_cache[7] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "最近命中", -1)),
                          _createElementVNode("div", _hoisted_5, _toDisplayString(status.last_report ? status.last_report.hit_count : 0), 1)
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
                default: _withCtx(() => [...(_cache[8] || (_cache[8] = [
                  _createTextVNode("最近一次扫描报告", -1)
                ]))]),
                _: 1
              }),
              (status.last_report)
                ? (_openBlock(), _createBlock(_component_VCardText, { key: 0 }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_6, " 共扫描 " + _toDisplayString(status.last_report.scanned_count) + " 条订阅，命中 " + _toDisplayString(status.last_report.hit_count) + " 条。 ", 1),
                      (status.last_report.hits?.length)
                        ? (_openBlock(), _createElementBlock("div", _hoisted_7, [
                            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(status.last_report.hits, (hit, i) => {
                              return (_openBlock(), _createElementBlock("div", {
                                key: i,
                                class: "d-flex align-center py-1",
                                style: {"border-bottom":"1px solid rgba(0,0,0,0.08)"}
                              }, [
                                _createElementVNode("div", _hoisted_8, [
                                  _createTextVNode(_toDisplayString(hit.name), 1),
                                  (hit.season)
                                    ? (_openBlock(), _createElementBlock("span", _hoisted_9, " S" + _toDisplayString(hit.season), 1))
                                    : _createCommentVNode("", true)
                                ]),
                                _createVNode(_component_VChip, {
                                  size: "small",
                                  color: hit.action === 'delete' ? 'error' : 'warning'
                                }, {
                                  default: _withCtx(() => [
                                    _createTextVNode(_toDisplayString(hit.action === 'delete' ? '已删除' : '已暂停'), 1)
                                  ]),
                                  _: 2
                                }, 1032, ["color"])
                              ]))
                            }), 128))
                          ]))
                        : (_openBlock(), _createElementBlock("div", _hoisted_10, "暂无命中记录"))
                    ]),
                    _: 1
                  }))
                : (_openBlock(), _createBlock(_component_VCardText, {
                    key: 1,
                    class: "text-caption text-medium-emphasis"
                  }, {
                    default: _withCtx(() => [...(_cache[9] || (_cache[9] = [
                      _createTextVNode("尚未执行过扫描", -1)
                    ]))]),
                    _: 1
                  }))
            ]),
            _: 1
          })
        ], 64))
  ]))
}
}

};

export { _sfc_main as default };
