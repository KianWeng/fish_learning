import request from './request.js'

export function listSubjects() {
  return request.get('/subjects')
}

export function getSubject(id) {
  return request.get(`/subjects/${id}`)
}

export function createSubject(data) {
  return request.post('/subjects', data)
}

export function updateSubject(id, data) {
  return request.put(`/subjects/${id}`, data)
}

export function deleteSubject(id) {
  return request.delete(`/subjects/${id}`)
}
