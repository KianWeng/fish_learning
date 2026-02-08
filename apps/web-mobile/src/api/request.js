import { API_BASE_URL } from '@/config.js'

const TOKEN_KEY = 'token'

function request(options) {
  const url = (options.url.startsWith('http') ? options.url : API_BASE_URL + options.url)
  const header = { 'Content-Type': 'application/json', ...options.header }
  try {
    const token = uni.getStorageSync(TOKEN_KEY)
    if (token) header['Authorization'] = 'Bearer ' + token
  } catch (e) {}
  return new Promise((resolve, reject) => {
    uni.request({
      url,
      method: options.method || 'GET',
      data: options.data,
      header,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          reject(new Error(res.data?.detail || '请求失败'))
        }
      },
      fail: reject
    })
  })
}

export default {
  get: (url, data) => request({ url, method: 'GET', data }),
  post: (url, data) => request({ url, method: 'POST', data }),
  put: (url, data) => request({ url, method: 'PUT', data }),
  delete: (url) => request({ url, method: 'DELETE' })
}
