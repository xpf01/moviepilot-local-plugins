import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,Fragment:_Fragment,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "pa-4" };
const _hoisted_2 = { class: "text-h6" };
const _hoisted_3 = { class: "text-h6" };
const _hoisted_4 = { class: "text-subtitle-2 mb-1" };
const _hoisted_5 = { class: "text-body-2" };

const {onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'SeriesOrganizer' },
},
  emits: ['close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const loading = ref(false);
const message = reactive({ text: '', type: 'info' });
const status = reactive({ enabled: false, notify: true, dry_run: false, series_count: 0, series_map: {} });

async function loadStatus() {
  loading.value = true;
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'SeriesOrganizer'}/status`);
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
          icon: "mdi-folder-multiple",
          color: "primary",
          class: "me-2"
        }),
        _cache[1] || (_cache[1] = _createElementVNode("div", { class: "text-h6" }, "系列自动归组", -1)),
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
          default: _withCtx(() => [...(_cache[2] || (_cache[2] = [
            _createTextVNode(" 插件未启用，请在「配置」中启用。 ", -1)
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
                        default: _withCtx(() => [...(_cache[3] || (_cache[3] = [
                          _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "启用状态", -1),
                          _createElementVNode("div", { class: "text-h6" }, "已启用", -1)
                        ]))]),
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
                          _cache[4] || (_cache[4] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "通知提示", -1)),
                          _createElementVNode("div", _hoisted_2, _toDisplayString(status.notify ? '开启' : '关闭'), 1)
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
                          _cache[5] || (_cache[5] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "演练模式", -1)),
                          _createElementVNode("div", _hoisted_3, _toDisplayString(status.dry_run ? '开启' : '关闭'), 1)
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
              _createVNode(_component_VCardText, null, {
                default: _withCtx(() => [
                  _createElementVNode("div", _hoisted_4, "系列映射表（" + _toDisplayString(status.series_count) + " 个系列）", 1),
                  _createElementVNode("div", _hoisted_5, _toDisplayString(Object.keys(status.series_map || {}).join('、') || '未配置'), 1)
                ]),
                _: 1
              })
            ]),
            _: 1
          })
        ], 64))
  ]))
}
}

};

export { _sfc_main as default };
