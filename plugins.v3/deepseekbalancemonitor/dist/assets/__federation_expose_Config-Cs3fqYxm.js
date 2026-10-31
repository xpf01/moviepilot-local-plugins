import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "pa-4" };
const _hoisted_2 = { class: "d-flex justify-end mt-4" };

const {onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Config',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'DeepSeekBalanceMonitor' },
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
  interval_minutes: 60,
  threshold: 5.0,
  api_key: '',
  base_url: 'https://api.deepseek.com',
  balance_url: '',
  timeout: 20,
  use_proxy: false,
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
      interval_minutes: Number(config.interval_minutes) || 60,
      threshold: Number(config.threshold) || 5.0,
      api_key: String(config.api_key || '').trim(),
      base_url: String(config.base_url || '').trim(),
      balance_url: String(config.balance_url || '').trim(),
      timeout: Number(config.timeout) || 20,
      use_proxy: Boolean(config.use_proxy),
      onlyonce: Boolean(config.onlyonce),
    };
    const response = await props.api.put(`plugin/${props.pluginId || 'DeepSeekBalanceMonitor'}`, payload);
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
          icon: "mdi-currency-cny",
          color: "primary",
          class: "me-2"
        }),
        _cache[10] || (_cache[10] = _createElementVNode("div", { class: "text-h6" }, "DeepSeek余额监控配置", -1)),
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
      default: _withCtx(() => [...(_cache[11] || (_cache[11] = [
        _createTextVNode(" 监控总可用余额（充值 + 赠金），低于阈值或账户欠费时通知告警，充值恢复后再次跌破才重新提醒。API Key 留空时自动复用系统 LLM 配置。 ", -1)
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
          md: "4"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_VTextField, {
              modelValue: config.interval_minutes,
              "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => ((config.interval_minutes) = $event)),
              modelModifiers: { number: true },
              label: "轮询间隔(分钟)",
              type: "number",
              variant: "outlined",
              placeholder: "60"
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
              modelValue: config.threshold,
              "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => ((config.threshold) = $event)),
              modelModifiers: { number: true },
              label: "告警阈值(余额)",
              type: "number",
              variant: "outlined",
              placeholder: "5"
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
              modelValue: config.timeout,
              "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => ((config.timeout) = $event)),
              modelModifiers: { number: true },
              label: "请求超时(秒)",
              type: "number",
              variant: "outlined",
              placeholder: "20"
            }, null, 8, ["modelValue"])
          ]),
          _: 1
        }),
        _createVNode(_component_VCol, { cols: "12" }, {
          default: _withCtx(() => [
            _createVNode(_component_VTextField, {
              modelValue: config.api_key,
              "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => ((config.api_key) = $event)),
              label: "API Key（留空复用系统 LLM 配置）",
              type: "password",
              variant: "outlined"
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
              modelValue: config.base_url,
              "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => ((config.base_url) = $event)),
              label: "Base URL",
              variant: "outlined",
              placeholder: "https://api.deepseek.com"
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
              modelValue: config.balance_url,
              "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => ((config.balance_url) = $event)),
              label: "余额接口（留空自动拼接 /user/balance）",
              variant: "outlined"
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
              modelValue: config.use_proxy,
              "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => ((config.use_proxy) = $event)),
              label: "使用系统代理访问",
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
        default: _withCtx(() => [...(_cache[12] || (_cache[12] = [
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
