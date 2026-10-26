import { createApp } from 'vue'

// 联邦远程组件仅作为入口导出，不独立挂载，由 MoviePilot 前端按需加载。
export async function bootstrap() {
  return { app: null }
}

