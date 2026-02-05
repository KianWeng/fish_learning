import request from './request.js'

export function listChapters(subjectId) {
  return request.get('/chapters', { subject_id: subjectId })
}

export function getChapter(id) {
  return request.get(`/chapters/${id}`)
}

export function createChapter(data) {
  return request.post('/chapters', data)
}

export function updateChapter(id, data) {
  return request.put(`/chapters/${id}`, data)
}

export function deleteChapter(id) {
  return request.delete(`/chapters/${id}`)
}
