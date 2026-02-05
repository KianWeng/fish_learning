import request from './request.js'

const BASE_URL = typeof window !== 'undefined' && window.location.hostname === 'localhost' ? '/api' : 'http://localhost:8000'

/**
 * 上传 PDF 并导入错题。H5 传入 { file, subjectId, chapterId } 其中 file 为 File 对象；
 * 小程序/App 传入 { filePath, subjectId, chapterId }。
 */
export function importPdf(options) {
  const { subjectId, chapterId } = options
  if (options.file) {
    const form = new FormData()
    form.append('file', options.file)
    form.append('subject_id', String(subjectId))
    if (chapterId != null) form.append('chapter_id', String(chapterId))
    return fetch(`${BASE_URL}/upload/pdf/import`, {
      method: 'POST',
      body: form,
    }).then((res) => {
      if (!res.ok) return res.json().then((d) => Promise.reject(new Error(d.detail || '导入失败')))
      return res.json()
    })
  }
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${BASE_URL}/upload/pdf/import`,
      filePath: options.filePath,
      name: 'file',
      formData: { subject_id: String(subjectId), chapter_id: chapterId != null ? String(chapterId) : '' },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
            resolve(data)
          } catch (e) {
            reject(e)
          }
        } else {
          try {
            const d = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
            reject(new Error(d.detail || '导入失败'))
          } catch {
            reject(new Error('导入失败'))
          }
        }
      },
      fail: reject,
    })
  })
}
