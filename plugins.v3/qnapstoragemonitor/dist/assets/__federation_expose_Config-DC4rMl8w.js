import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "pa-4" };
const _hoisted_2 = { class: "d-flex justify-end mt-4" };

const {onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'QnapStorageMonitor' },
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
  host: '192.168.1.11',
  port: 22,
  username: '',
  password: '',
  interval_hours: 12,
  stop_threshold_gb: 500,
  resume_threshold_gb: 2000,
  auto_pause_download: true,
  monitor_all: false,
  onlyonce: false,
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
    const payload = {
      enabled: Boolean(config.enabled),
      host: String(config.host || '').trim(),
      port: Number(config.port) || 22,
      username: String(config.username || '').trim(),
      password: String(config.password || ''),
      interval_hours: Number(config.interval_hours) || 12,
      stop_threshold_gb: Number(config.stop_threshold_gb) || 500,
      resume_threshold_gb: Number(config.resume_threshold_gb) || 2000,
      auto_pause_download: Boolean(config.auto_pause_download),
      monitor_all: Boolean(config.monitor_all),
      onlyonce: Boolean(config.onlyonce),
    };
    const response = await props.api.put(`plugin/${props.pluginId || 'QnapStorageMonitor'}`, payload);
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
  const _component_VRow = _resolveComponent("VRow");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createVNode(_component_VToolbar, {
      density: "comfortable",
      color: "transparent",
      class: "px-0"
    }, {
      default: _withCtx(() => [
        _createVNode(_component_VIcon, {
          icon: "mdi-database",
          color: "primary",
          class: "me-2"
        }),
        _cache[12] || (_cache[12] = _createElementVNode("div", { class: "text-h6" }, "QNAP存储池监控配置", -1)),
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
      default: _withCtx(() => [...(_cache[13] || (_cache[13] = [
        _createTextVNode(" 低于「停止下载阈值」暂停下载器任务（保留做种），高于「恢复下载阈值」自动恢复。仅支持 Transmission 下载器。 ", -1)
      ]))]),
      _: 1
    }),
    _createVNode(_component_VRow, { dense: "" }, {
      default: _withCtx(() => [
        _createVNode(_component_VCol, {
          cols: "12",
          md: "6"
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
          md: "6"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VSwitch, {
              modelValue: config.onlyonce,
              "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => ((config.onlyonce) = $event)),
              label: "立即运行一次",
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
              modelValue: config.host,
              "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.host) = $event)),
              label: "QNAP 地址",
              variant: "outlined",
              placeholder: "192.168.1.11"
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
              modelValue: config.port,
              "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.port) = $event)),
              modelModifiers: { number: true },
              label: "SSH 端口",
              type: "number",
              variant: "outlined",
              placeholder: "22"
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
              "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.username) = $event)),
              label: "SSH 用户名",
              variant: "outlined",
              placeholder: "admin"
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
              "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.password) = $event)),
              label: "SSH 密码",
              type: "password",
              variant: "outlined"
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
              modelValue: config.interval_hours,
              "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((config.interval_hours) = $event)),
              modelModifiers: { number: true },
              label: "轮询间隔(小时)",
              type: "number",
              variant: "outlined",
              placeholder: "12"
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
              modelValue: config.stop_threshold_gb,
              "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((config.stop_threshold_gb) = $event)),
              modelModifiers: { number: true },
              label: "停止下载阈值(GB)",
              type: "number",
              variant: "outlined",
              placeholder: "500"
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
              modelValue: config.resume_threshold_gb,
              "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((config.resume_threshold_gb) = $event)),
              modelModifiers: { number: true },
              label: "恢复下载阈值(GB)",
              type: "number",
              variant: "outlined",
              placeholder: "2000"
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
              modelValue: config.auto_pause_download,
              "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => ((config.auto_pause_download) = $event)),
              label: "低于阈值时自动暂停下载",
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
              modelValue: config.monitor_all,
              "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => ((config.monitor_all) = $event)),
              label: "监控全部存储池",
              "hide-details": ""
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
        default: _withCtx(() => [...(_cache[14] || (_cache[14] = [
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
