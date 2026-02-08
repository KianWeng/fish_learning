import { defineConfig, loadEnv } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiBase = env.VITE_API_BASE_URL || 'http://192.168.3.22:8000'

  return {
    plugins: [uni()],
    define: {
      // 注入 API 地址，避免源码使用 import.meta.env 导致微信小程序报 define is not defined
      __VITE_API_BASE_URL__: JSON.stringify(apiBase),
      // 小程序环境可能缺少 process，按需注入
      'process.env.NODE_ENV': JSON.stringify(mode === 'production' ? 'production' : 'development')
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: apiBase,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    }
  }
})
