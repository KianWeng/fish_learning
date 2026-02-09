/**
 * 错题本封面：有则用 subject.cover_url，无则用默认封面（错题本示意图）
 */
import { API_BASE_URL } from '@/config.js'

// 默认封面：内联 SVG 转 data URL，不依赖静态路径，<image> 在各端都能加载
const DEFAULT_COVER_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300"><defs><linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#E3F2FD"/><stop offset="100%" style="stop-color:#BBDEFB"/></linearGradient></defs><rect width="400" height="300" fill="url(#bg)"/><g transform="translate(120,60)"><rect x="0" y="0" width="160" height="120" rx="8" fill="#fff" stroke="#4A90E2" stroke-width="3"/><line x1="80" y1="0" x2="80" y2="120" stroke="#4A90E2" stroke-width="2"/><rect x="20" y="20" width="50" height="6" rx="2" fill="#4A90E2" opacity="0.6"/><rect x="20" y="35" width="50" height="6" rx="2" fill="#4A90E2" opacity="0.4"/><rect x="90" y="20" width="50" height="6" rx="2" fill="#4A90E2" opacity="0.6"/><rect x="90" y="35" width="50" height="6" rx="2" fill="#4A90E2" opacity="0.4"/></g><text x="200" y="220" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#4A90E2" font-weight="bold">错题本</text></svg>`

function svgToDataUrl(svg) {
  const encoded = encodeURIComponent(svg)
  return `data:image/svg+xml,${encoded}`
}

export const DEFAULT_COVER_URL = svgToDataUrl(DEFAULT_COVER_SVG)

/**
 * 获取错题本（科目）的封面图 URL：有自定义封面则返回完整 URL，否则返回默认封面
 */
export function getSubjectCoverUrl(subject, apiBase = API_BASE_URL) {
  const url = subject?.cover_url
  if (!url || typeof url !== 'string') return DEFAULT_COVER_URL
  return url.startsWith('http') ? url : (apiBase || '').replace(/\/$/, '') + (url.startsWith('/') ? url : '/' + url)
}
