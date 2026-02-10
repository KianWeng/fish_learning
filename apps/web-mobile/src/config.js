/**
 * 后端 API 基地址（可配置）
 *
 * 配置方式：在 .env 中设置 VITE_API_BASE_URL（构建时由 vite define 注入）
 * - H5 本地开发：可设为 /api 走 vite 代理
 * - 小程序/真机：必须为完整 HTTPS 地址
 *
 * 注：不访问 window/import.meta，避免小程序逻辑层执行时报错或栈异常
 */
const DEFAULT_API_BASE_URL = 'http://192.168.3.22:8000'

export const API_BASE_URL =
  typeof __VITE_API_BASE_URL__ !== 'undefined' ? __VITE_API_BASE_URL__ : DEFAULT_API_BASE_URL

/** 微信小程序激励视频广告位 ID（流量主-广告位），未配置则页面不创建广告 */
export const AD_REWARD_UNIT_ID =
  typeof __VITE_AD_REWARD_UNIT_ID__ !== 'undefined' ? __VITE_AD_REWARD_UNIT_ID__ : ''
