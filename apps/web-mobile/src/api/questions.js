import request from './request.js'
import { API_BASE_URL } from '@/config.js'

export function listQuestions(params = {}) {
  return request.get('/questions', params)
}

export function getQuestion(id) {
  return request.get(`/questions/${id}`)
}

export function deleteQuestion(id) {
  return request.delete(`/questions/${id}`)
}

export function updateQuestion(id, data) {
  return request.patch(`/questions/${id}`, data)
}

export function createQuestion(data) {
  return request.post('/questions', data)
}

/** 仅上传图片，不分析。用于手动输入/解析附图等，需登录态 */
export function uploadImage(filePath) {
  return new Promise((resolve, reject) => {
    const url = API_BASE_URL + '/upload/image'
    const header = {}
    try {
      const token = uni.getStorageSync('token')
      if (token) header['Authorization'] = 'Bearer ' + token
    } catch (e) {}
    if (url.startsWith('http') && typeof uni !== 'undefined') {
      uni.uploadFile({
        url,
        filePath,
        name: 'file',
        header,
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            try {
              const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
              resolve(data)
            } catch (e) {
              reject(e)
            }
          } else {
            reject(new Error(res.data || '上传失败'))
          }
        },
        fail: reject
      })
    } else {
      reject(new Error('请在真机或模拟器中上传'))
    }
  })
}

export function uploadAndAnalyzeImage(filePath) {
  return new Promise((resolve, reject) => {
    const url = API_BASE_URL + '/upload/image/analyze'
    const header = {}
    try {
      const token = uni.getStorageSync('token')
      if (token) header['Authorization'] = 'Bearer ' + token
    } catch (e) {}
    if (url.startsWith('http') && typeof uni !== 'undefined') {
      uni.uploadFile({
        url,
        filePath,
        name: 'file',
        header,
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            try {
              const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
              resolve(data)
            } catch (e) {
              reject(e)
            }
          } else {
            reject(new Error(res.data || '上传失败'))
          }
        },
        fail: reject
      })
    } else {
      reject(new Error('请在真机或模拟器中上传'))
    }
  })
}
