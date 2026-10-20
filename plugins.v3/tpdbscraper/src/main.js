import { createApp } from 'vue'

// 联邦远程组件仅作为入口导出，不独立挂载。
export async function bootstrap() {
  return { app: null }
}
