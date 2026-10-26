import { importShared } from './__federation_fn_import-JrT3xvdd.js';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,Fragment:_Fragment,createElementBlock:_createElementBlock} = await importShared('vue');


const _hoisted_1 = { class: "pa-4" };
const _hoisted_2 = { class: "text-body-2" };
const _hoisted_3 = { class: "d-flex justify-end mt-4" };

const {onMounted,reactive,ref} = await importShared('vue');



const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'QnapStorageMonitor' },
},
  emits: ['close'],
  setup(__props, { emit: __emit }) {

const props = __props;

const emit = __emit;
const loading = ref(false);
const running = ref(false);
const message = reactive({ text: '', type: 'info' });
const status = reactive({ enabled: false, download_paused: false, last_report: '' });

function showMessage(text, type = 'info') {
  message.text = text;
  message.type = type;
  if (text) setTimeout(() => { if (message.text === text) message.text = ''; }, 4000);
}

async function loadStatus() {
  loading.value = true;
  try {
    const response = await props.api.get(`plugin/${props.pluginId || 'QnapStorageMonitor'}/status`);
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
    const response = await props.api.post(`plugin/${props.pluginId || 'QnapStorageMonitor'}/check_now`, {});
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
        _cache[1] || (_cache[1] = _createElementVNode("div", { class: "text-h6" }, "QNAP存储池监控", -1)),
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
          _createVNode(_component_VAlert, {
            type: status.download_paused ? 'warning' : 'success',
            variant: "tonal",
            density: "compact",
            class: "mb-4"
          }, {
            default: _withCtx(() => [
              _createTextVNode(" 下载任务状态：" + _toDisplayString(status.download_paused ? '已暂停（等待容量恢复）' : '正常'), 1)
            ]),
            _: 1
          }, 8, ["type"]),
          _createVNode(_component_VCard, { variant: "outlined" }, {
            default: _withCtx(() => [
              _createVNode(_component_VCardText, null, {
                default: _withCtx(() => [
                  _cache[3] || (_cache[3] = _createElementVNode("div", { class: "text-subtitle-2 mb-1" }, "最近检查结果", -1)),
                  _createElementVNode("div", _hoisted_2, _toDisplayString(status.last_report || '尚未执行检查'), 1)
                ]),
                _: 1
              })
            ]),
            _: 1
          }),
          _createElementVNode("div", _hoisted_3, [
            _createVNode(_component_VBtn, {
              color: "primary",
              "prepend-icon": "mdi-play",
              loading: running.value,
              onClick: checkNow
            }, {
              default: _withCtx(() => [...(_cache[4] || (_cache[4] = [
                _createTextVNode("立即检查", -1)
              ]))]),
              _: 1
            }, 8, ["loading"])
          ])
        ], 64))
  ]))
}
}

};

export { _sfc_main as default };
