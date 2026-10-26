import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,renderList:_renderList,Fragment:_Fragment,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "pa-4" };
const _hoisted_2 = { class: "d-flex justify-end mt-4" };

const {onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'MediaExplore' },
  initialConfig: { type: Object, default: () => ({}) },
},
  emits: ['save', 'close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const saving = ref(false);
const message = reactive({ text: '', type: 'info' });

const MODULES = [
  { key: 'tencentvideo', label: '腾讯视频' },
  { key: 'bilibili', label: '哔哩哔哩' },
  { key: 'cctv', label: 'CCTV' },
  { key: 'mangguo', label: '芒果TV' },
  { key: 'bangumidaily', label: 'Bangumi每日放送' },
  { key: 'migu', label: '咪咕视频' },
];

const defaults = {
  tencentvideo_enabled: false,
  bilibili_enabled: false,
  cctv_enabled: false,
  mangguo_enabled: false,
  bangumidaily_enabled: false,
  migu_enabled: false,
  iqiyi_enabled: false,
  iqiyi_cookie: '',
  iqiyi_refresh_cron: '',
  maoyan_enabled: false,
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
  saving.value = true;
  try {
    const payload = {};
    for (const m of MODULES) payload[`${m.key}_enabled`] = Boolean(config[`${m.key}_enabled`]);
    payload.iqiyi_enabled = Boolean(config.iqiyi_enabled);
    payload.iqiyi_cookie = String(config.iqiyi_cookie || '');
    payload.iqiyi_refresh_cron = String(config.iqiyi_refresh_cron || '');
    payload.maoyan_enabled = Boolean(config.maoyan_enabled);
    const response = await props.api.put(`plugin/${props.pluginId || 'MediaExplore'}`, payload);
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
  Object.assign(config, defaults, props.initialConfig || {});
});

return (_ctx, _cache) => {
  const _component_VIcon = _resolveComponent("VIcon");
  const _component_VSpacer = _resolveComponent("VSpacer");
  const _component_VBtn = _resolveComponent("VBtn");
  const _component_VToolbar = _resolveComponent("VToolbar");
  const _component_VDivider = _resolveComponent("VDivider");
  const _component_VAlert = _resolveComponent("VAlert");
  const _component_VCardTitle = _resolveComponent("VCardTitle");
  const _component_VSwitch = _resolveComponent("VSwitch");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VRow = _resolveComponent("VRow");
  const _component_VCardText = _resolveComponent("VCardText");
  const _component_VCard = _resolveComponent("VCard");
  const _component_VTextField = _resolveComponent("VTextField");

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
        _cache[5] || (_cache[5] = _createElementVNode("div", { class: "text-h6" }, "媒体探索聚合配置", -1)),
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
    _createVNode(_component_VCard, {
      variant: "outlined",
      class: "mb-4"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCardTitle, { class: "text-subtitle-1" }, {
          default: _withCtx(() => [...(_cache[6] || (_cache[6] = [
            _createTextVNode("探索源开关", -1)
          ]))]),
          _: 1
        }),
        _createVNode(_component_VCardText, null, {
          default: _withCtx(() => [
            _createVNode(_component_VRow, { dense: "" }, {
              default: _withCtx(() => [
                (_openBlock(), _createElementBlock(_Fragment, null, _renderList(MODULES, (m) => {
                  return _createVNode(_component_VCol, {
                    key: m.key,
                    cols: "12",
                    md: "4"
                  }, {
                    default: _withCtx(() => [
                      _createVNode(_component_VSwitch, {
                        modelValue: config[`${m.key}_enabled`],
                        "onUpdate:modelValue": $event => ((config[`${m.key}_enabled`]) = $event),
                        label: `启用${m.label}探索源`,
                        "hide-details": ""
                      }, null, 8, ["modelValue", "onUpdate:modelValue", "label"])
                    ]),
                    _: 2
                  }, 1024)
                }), 64)),
                _createVNode(_component_VCol, {
                  cols: "12",
                  md: "4"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_VSwitch, {
                      modelValue: config.iqiyi_enabled,
                      "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => ((config.iqiyi_enabled) = $event)),
                      label: "启用爱奇艺探索源",
                      "hide-details": ""
                    }, null, 8, ["modelValue"])
                  ]),
                  _: 1
                }),
                _createVNode(_component_VCol, {
                  cols: "12",
                  md: "4"
                }, {
                  default: _withCtx(() => [
                    _createVNode(_component_VSwitch, {
                      modelValue: config.maoyan_enabled,
                      "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.maoyan_enabled) = $event)),
                      label: "启用猫眼TOP30探索源",
                      "hide-details": ""
                    }, null, 8, ["modelValue"])
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
      class: "mb-4"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VCardTitle, { class: "text-subtitle-1" }, {
          default: _withCtx(() => [...(_cache[7] || (_cache[7] = [
            _createTextVNode("爱奇艺配置", -1)
          ]))]),
          _: 1
        }),
        _createVNode(_component_VCardText, null, {
          default: _withCtx(() => [
            _createVNode(_component_VTextField, {
              modelValue: config.iqiyi_cookie,
              "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.iqiyi_cookie) = $event)),
              label: "爱奇艺 Cookie（可选）",
              variant: "outlined",
              hint: "留空则由 CloakBrowser 自动获取；失效时可手动填入 Cookie",
              "persistent-hint": ""
            }, null, 8, ["modelValue"]),
            _createVNode(_component_VTextField, {
              modelValue: config.iqiyi_refresh_cron,
              "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.iqiyi_refresh_cron) = $event)),
              label: "Cookie 定时刷新周期（Cron 表达式，可选）",
              variant: "outlined",
              hint: "例如 0 */2 * * *（每 2 小时）",
              "persistent-hint": ""
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        })
      ]),
      _: 1
    }),
    _createElementVNode("div", _hoisted_2, [
      _createVNode(_component_VBtn, {
        color: "primary",
        loading: saving.value,
        onClick: saveConfig
      }, {
        default: _withCtx(() => [...(_cache[8] || (_cache[8] = [
          _createTextVNode("保存配置", -1)
        ]))]),
        _: 1
      }, 8, ["loading"])
    ])
  ]))
}
}

};

export { _sfc_main as default };
