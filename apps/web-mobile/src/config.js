/**
 * 后端 API 基地址（可配置）
 *
 * 配置方式（按优先级）：
 * 1. 环境变量：在 .env 或 .env.local 中设置 VITE_API_BASE_URL（构建时由 vite define 注入）
 * 2. 默认：浏览器且 host 为 localhost 时使用 /api（走 vite 代理），否则使用下方默认直连地址
 *
 * 修改后端地址时：改 .env 中的 VITE_API_BASE_URL，或直接改本文件中的 DEFAULT_API_BASE_URL
 * 注：不使用 import.meta.env 以避免微信小程序编译报 define is not defined
 */
const isLocalhost =
  typeof window !== 'undefined' && window.location?.hostname === 'localhost'

const DEFAULT_API_BASE_URL = 'http://192.168.3.22:8000'

// 构建时由 vite.config.js define 注入；小程序环境无 import.meta 故用全局注入
const envApiBase = typeof __VITE_API_BASE_URL__ !== 'undefined' ? __VITE_API_BASE_URL__ : DEFAULT_API_BASE_URL

export const API_BASE_URL = isLocalhost ? '/api' : envApiBase
