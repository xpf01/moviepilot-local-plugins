import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "pa-4" };
const _hoisted_2 = { class: "d-flex justify-end mt-4" };

const {onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'TpdbScraper' },
  initialConfig: { type: Object, default: () => ({}) },
},
  emits: ['save', 'close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const saving = ref(false);
const message = reactive({ text: '', type: 'info' });

const defaults = {
  enabled: false,
  api_token: '',
  tpdb_use_proxy: false,
  tpdb_proxy: 'http://192.168.1.2:7893',
  library_dirs: '/media/XXX',
  overwrite_nfo: false,
  download_poster: true,
  stashdb_enabled: false,
  stashdb_api_key: '',
  extra_stashbox_endpoints: '',
  stashbox_use_proxy: false,
  stashbox_proxy: 'http://192.168.1.2:7893',
  scrape_hour: 2,
  batch_size: 50,
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
  if (config.enabled && !String(config.api_token || '').trim()) {
    showMessage('启用插件前请填写 ThePornDB API Token', 'error');
    return
  }
  saving.value = true;
  try {
    const payload = {
      enabled: Boolean(config.enabled),
      api_token: String(config.api_token || '').trim(),
      tpdb_use_proxy: Boolean(config.tpdb_use_proxy),
      tpdb_proxy: String(config.tpdb_proxy || '').trim(),
      library_dirs: String(config.library_dirs || '').trim(),
      overwrite_nfo: Boolean(config.overwrite_nfo),
      download_poster: Boolean(config.download_poster),
      stashdb_enabled: Boolean(config.stashdb_enabled),
      stashdb_api_key: String(config.stashdb_api_key || '').trim(),
      extra_stashbox_endpoints: String(config.extra_stashbox_endpoints || ''),
      stashbox_use_proxy: Boolean(config.stashbox_use_proxy),
      stashbox_proxy: String(config.stashbox_proxy || '').trim(),
      scrape_hour: Number(config.scrape_hour) || 2,
      batch_size: Number(config.batch_size) || 50,
    };
    const response = await props.api.put(`plugin/${props.pluginId || 'TpdbScraper'}`, payload);
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
  const _component_VSwitch = _resolveComponent("VSwitch");
  const _component_VCol = _resolveComponent("VCol");
  const _component_VTextField = _resolveComponent("VTextField");
  const _component_VTextarea = _resolveComponent("VTextarea");
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
        _cache[15] || (_cache[15] = _createElementVNode("div", { class: "text-h6" }, "ThePornDB 成人刮削配置", -1)),
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
      default: _withCtx(() => [...(_cache[16] || (_cache[16] = [
        _createTextVNode(" 本插件在 MoviePilot 端调用 ThePornDB 刮削成人内容元数据，NFO 落盘并下载海报；Jellyfin 侧保持只读，扫描即可读取。 ", -1)
      ]))]),
      _: 1
    }),
    _createVNode(_component_VRow, { dense: "" }, {
      default: _withCtx(() => [
        _createVNode(_component_VCol, { cols: "12" }, {
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
        _createVNode(_component_VCol, { cols: "12" }, {
          default: _withCtx(() => [
            _createVNode(_component_VTextField, {
              modelValue: config.api_token,
              "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.api_token) = $event)),
              label: "ThePornDB API Token",
              type: "password",
              variant: "outlined",
              hint: "在 theporndb.net 的 API Tokens 页创建，需 read 权限。",
              "persistent-hint": ""
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "6"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VSwitch, {
              modelValue: config.tpdb_use_proxy,
              "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.tpdb_use_proxy) = $event)),
              label: "ThePornDB 主源走代理",
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
              modelValue: config.tpdb_proxy,
              "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.tpdb_proxy) = $event)),
              label: "ThePornDB 代理地址",
              variant: "outlined",
              placeholder: "http://192.168.1.2:7893"
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, { cols: "12" }, {
          default: _withCtx(() => [
            _createVNode(_component_VTextarea, {
              modelValue: config.library_dirs,
              "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.library_dirs) = $event)),
              label: "媒体库目录（每行一个）",
              rows: "4",
              variant: "outlined",
              hint: "例如 /media/XXX",
              "persistent-hint": ""
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "6"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VSwitch, {
              modelValue: config.overwrite_nfo,
              "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.overwrite_nfo) = $event)),
              label: "覆盖已有 movie.nfo",
              color: "warning",
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
            _createVNode(_component_VSwitch, {
              modelValue: config.download_poster,
              "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((config.download_poster) = $event)),
              label: "下载海报 poster.jpg",
              color: "success",
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
            _createVNode(_component_VSwitch, {
              modelValue: config.stashdb_enabled,
              "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((config.stashdb_enabled) = $event)),
              label: "启用 StashDB 补充源",
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
              modelValue: config.stashdb_api_key,
              "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((config.stashdb_api_key) = $event)),
              label: "StashDB API Key",
              type: "password",
              variant: "outlined",
              hint: "在 stashdb.org 个人页复制（可选）",
              "persistent-hint": ""
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, { cols: "12" }, {
          default: _withCtx(() => [
            _createVNode(_component_VTextarea, {
              modelValue: config.extra_stashbox_endpoints,
              "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((config.extra_stashbox_endpoints) = $event)),
              label: "额外备用 Stash-box 端点（每行一个，格式 端点|APIKey）",
              rows: "3",
              variant: "outlined",
              hint: "https://fansdb.cc/graphql|你的key",
              "persistent-hint": ""
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, {
          cols: "12",
          md: "6"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VSwitch, {
              modelValue: config.stashbox_use_proxy,
              "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((config.stashbox_use_proxy) = $event)),
              label: "Stash-box 补充源走代理",
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
              modelValue: config.stashbox_proxy,
              "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => ((config.stashbox_proxy) = $event)),
              label: "Stash-box 代理地址",
              variant: "outlined",
              placeholder: "http://192.168.1.2:7893"
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
              modelValue: config.scrape_hour,
              "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => ((config.scrape_hour) = $event)),
              modelModifiers: { number: true },
              label: "每日刮削时间（小时，0-23）",
              type: "number",
              variant: "outlined",
              hint: "2 = 凌晨 2 点",
              "persistent-hint": ""
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
              modelValue: config.batch_size,
              "onUpdate:modelValue": _cache[14] || (_cache[14] = $event => ((config.batch_size) = $event)),
              modelModifiers: { number: true },
              label: "每轮刮削数量",
              type: "number",
              variant: "outlined",
              hint: "每轮最多处理的条目数",
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
        default: _withCtx(() => [...(_cache[17] || (_cache[17] = [
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
