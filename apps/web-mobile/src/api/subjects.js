import request from './request.js'

/** @param {{ course?: string }} params - course 按科目筛选，不传则全部 */
export function listSubjects(params = {}) {
  const course = params.course
  const url = course ? '/subjects?course=' + encodeURIComponent(course) : '/subjects'
  return request.get(url)
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

/** 按错题本导出 PDF，返回 { url, filename } */
export function exportSubjectPdf(id) {
  return request.post(`/subjects/${id}/export/pdf`)
}

/** 获取单本错题本学习报告，返回 { subject_name, report, knowledge_map, generated_at } */
export function getSubjectReport(id) {
  return request.get(`/subjects/${id}/report`)
}

/** 导出学习报告为 PDF，返回 { url, filename } */
export function exportReportPdf(id) {
  return request.post(`/subjects/${id}/report/export/pdf`)
}
