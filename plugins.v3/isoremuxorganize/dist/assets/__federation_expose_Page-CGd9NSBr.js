import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,toDisplayString:_toDisplayString,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "pa-4" };
const _hoisted_2 = { class: "text-body-2" };
const _hoisted_3 = { class: "text-h6" };
const _hoisted_4 = { class: "text-h6" };

const {onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'IsoRemuxOrganize' },
},
  emits: ['close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const loading = ref(false);
const status = reactive({
  enabled: false,
  scan_root: '',
  interval: 0,
  timeout: 0,
  notify: true,
  processed_count: 0,
});

async function loadStatus() {
  loading.value = true;
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'IsoRemuxOrganize'}/status`);
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
          icon: "mdi-disc",
          color: "primary",
          class: "me-2"
        }),
        _cache[1] || (_cache[1] = _createElementVNode("div", { class: "text-h6" }, "ISO原盘转封装", -1)),
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
    (!status.enabled)
      ? (_openBlock(), _createBlock(_component_VAlert, {
          key: 0,
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
      : (_openBlock(), _createBlock(_component_VRow, {
          key: 1,
          dense: ""
        }, {
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
                        _cache[3] || (_cache[3] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "扫描根目录", -1)),
                        _createElementVNode("div", _hoisted_2, _toDisplayString(status.scan_root || '未配置'), 1)
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
                        _cache[4] || (_cache[4] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "扫描间隔（秒）", -1)),
                        _createElementVNode("div", _hoisted_3, _toDisplayString(status.interval), 1)
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
                        _cache[5] || (_cache[5] = _createElementVNode("div", { class: "text-caption text-medium-emphasis" }, "已处理 ISO 数", -1)),
                        _createElementVNode("div", _hoisted_4, _toDisplayString(status.processed_count), 1)
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
        }))
  ]))
}
}

};

export { _sfc_main as default };
