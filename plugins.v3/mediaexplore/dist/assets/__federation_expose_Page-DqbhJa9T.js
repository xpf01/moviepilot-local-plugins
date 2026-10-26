import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock,toDisplayString:_toDisplayString} = await importShared('vue');


const _hoisted_1 = { class: "pa-4" };
const _hoisted_2 = { class: "d-flex align-center py-1" };
const _hoisted_3 = { class: "text-body-2" };

const {onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'MediaExplore' },
},
  emits: ['close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const loading = ref(false);
const status = reactive({ enabled: false, sources: {} });

const LABELS = {
  tencentvideo: '腾讯视频',
  bilibili: '哔哩哔哩',
  cctv: 'CCTV',
  mangguo: '芒果TV',
  bangumidaily: 'Bangumi每日放送',
  migu: '咪咕视频',
  iqiyi: '爱奇艺',
  maoyan: '猫眼TOP30',
};

async function loadStatus() {
  loading.value = true;
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'MediaExplore'}/status`);
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
  const _component_VCol = _resolveComponent("VCol");
  const _component_VRow = _resolveComponent("VRow");
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
          icon: "mdi-compass-outline",
          color: "primary",
          class: "me-2"
        }),
        _cache[1] || (_cache[1] = _createElementVNode("div", { class: "text-h6" }, "媒体探索聚合", -1)),
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
            _createTextVNode(" 尚未开启任何探索源，请在「配置」中开启。 ", -1)
          ]))]),
          _: 1
        }))
      : _createCommentVNode("", true),
    _createVNode(_component_VCard, { variant: "outlined" }, {
      default: _withCtx(() => [
        _createVNode(_component_VCardText, null, {
          default: _withCtx(() => [
            _cache[3] || (_cache[3] = _createElementVNode("div", { class: "text-subtitle-2 mb-2" }, "探索源状态", -1)),
            _createVNode(_component_VRow, { dense: "" }, {
              default: _withCtx(() => [
                (_openBlock(), _createElementBlock(_Fragment, null, _renderList(LABELS, (label, key) => {
                  return _createVNode(_component_VCol, {
                    key: key,
                    cols: "6",
                    md: "4"
                  }, {
                    default: _withCtx(() => [
                      _createElementVNode("div", _hoisted_2, [
                        _createVNode(_component_VIcon, {
                          icon: status.sources?.[key] ? 'mdi-check-circle' : 'mdi-circle-outline',
                          color: status.sources?.[key] ? 'success' : undefined,
                          class: "me-2",
                          size: "small"
                        }, null, 8, ["icon", "color"]),
                        _createElementVNode("span", _hoisted_3, _toDisplayString(label), 1)
                      ])
                    ]),
                    _: 2
                  }, 1024)
                }), 64))
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ]),
      _: 1
    })
  ]))
}
}

};

export { _sfc_main as default };
