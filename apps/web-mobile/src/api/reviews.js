import request from './request.js'

/** 今日待复习（兼容旧用法） */
export function getTodayReviews() {
  return request.get('/reviews/today')
}

/** 按状态获取复习列表：today=待复习 scheduled=已排期 new=未开始 all=全部 */
export function getReviewList(status = 'today') {
  return request.get('/reviews/list', { params: { status } })
}

/** 掌握度统计：{ total, mastered }，掌握度 = mastered / total * 100 */
export function getReviewStats() {
  return request.get('/reviews/stats')
}

export function submitReviewResult(questionId, rating) {
  return request.post(`/reviews/${questionId}/result`, { rating })
}
