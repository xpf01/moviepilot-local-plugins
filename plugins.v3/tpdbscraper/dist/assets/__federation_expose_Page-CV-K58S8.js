import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,Fragment:_Fragment,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "pa-4" };
const _hoisted_2 = { class: "text-h6" };
const _hoisted_3 = { class: "text-h6" };
const _hoisted_4 = { class: "text-body-2" };
const _hoisted_5 = { class: "text-subtitle-2 mb-1" };
const _hoisted_6 = { class: "text-body-2" };
const _hoisted_7 = { class: "d-flex justify-end mt-4" };

const {onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'TpdbScraper' },
},
  emits: ['close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const running = ref(false);
const message = reactive({ text: '', type: 'info' });
const status = reactive({ enabled: false, has_token: false, library_dirs: [], last_result: null });

function showMessage(text, type = 'info') {
  message.text = text;
  message.type = type;
  if (text) setTimeout(() => { if (message.text === text) message.text = ''; }, 4000);
}

async function loadStatus() {
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'TpdbScraper'}/status`);
    const result = response?.data ?? response;
    if (result?.success !== false) {
      Object.assign(status, result?.data ?? result ?? {});
    }
  } catch (error) {
    /* 忽略状态读取失败 */
  }
}

async function scrapeNow() {
  running.value = true;
  try {
    const response = await props.api.post(`plugin/${props.pluginId || 'TpdbScraper'}/scrape_now`, {});
    const result = response?.data ?? response;
    if (result?.success === false) throw new Error(result.message || '刮削失败')
    const data = result?.data ?? {};
    showMessage(`刮削完成：共 ${data.total ?? 0}，命中 ${data.matched ?? 0}，失败 ${data.failed ?? 0}`, 'success');
    await loadStatus();
  } catch (error) {
    showMessage(error?.message || '刮削失败', 'error');
  } finally {
    running.value = false;
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

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VToolbar, {
      density: "comfortable",
      color: "transparent",
      class: "px-0"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VIcon, {
          icon: "mdi-movie-search",
          color: "primary",
          class: "me-2"
        }),
        _cache[1] || (_cache[1] = _createElementVNode("div", { class: "text-h6" }, "ThePornDB 成人刮削", -1)),
        _createVNode(_component_VSpacer),
        _createVNode(_component_VBtn, {
          icon: "mdi-refresh",
          variant: "text",
          title: "刷新状态",
          onClick: loadStatus
        }),
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
          default: _withCtx(() => [...(_cache[2] || (_cache[2] = [
            _createTextVNode(" 插件未启用，请在「配置」中启用并填写 API Token。 ", -1)
          ]))]),
          _: 1
        }))
      : (_openBlock(), _createElementBlock(_Fragment, { key: 2 }, [
          _createVNode(_component_VRow, { dense: "" }, {
            default: _withCtx(() => [
              _createVNode(_component_VCol, {
                cols: "12",
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_VCard, { variant: "outlined" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VCardText, null, {
                        default: _withCtx(() => [
                          _cache[3] || (_cache[3] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "启用状态", -1)),
                          _createElementVNode("div", _hoisted_2, _toDisplayString(status.enabled ? '已启用' : '未启用'), 1)
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
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_VCard, { variant: "outlined" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VCardText, null, {
                        default: _withCtx(() => [
                          _cache[4] || (_cache[4] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "API Token", -1)),
                          _createElementVNode("div", _hoisted_3, _toDisplayString(status.has_token ? '已配置' : '未配置'), 1)
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
                md: "4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_VCard, { variant: "outlined" }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VCardText, null, {
                        default: _withCtx(() => [
                          _cache[5] || (_cache[5] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "刮削目录", -1)),
                          _createElementVNode("div", _hoisted_4, _toDisplayString((status.library_dirs || []).join(', ') || '未配置'), 1)
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
          (status.last_result)
            ? (_openBlock(), _createBlock(_component_VCard, {
                key: 0,
                variant: "outlined",
                class: "mt-4"
              }, {
                default: _withCtx(() => [
                  _createVNode(_component_VCardText, null, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_5, "上次刮削结果（" + _toDisplayString(status.last_result.finished_at) + "）", 1),
                      _createElementVNode("div", _hoisted_6, " 共 " + _toDisplayString(status.last_result.total ?? 0) + " 个条目，命中 " + _toDisplayString(status.last_result.matched ?? 0) + "， 失败 " + _toDisplayString(status.last_result.failed ?? 0), 1)
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }))
            : _createCommentVNode("", true)
        ], 64)),
    _createElementVNode("div", _hoisted_7, [
      _createVNode(_component_VBtn, {
        color: "primary",
        "prepend-icon": "mdi-play",
        loading: running.value,
        onClick: scrapeNow
      }, {
        default: _withCtx(() => [...(_cache[6] || (_cache[6] = [
          _createTextVNode("立即全库刮削", -1)
        ]))]),
        _: 1
      }, 8, ["loading"])
    ])
  ]))
}
}

};

export { _sfc_main as default };
