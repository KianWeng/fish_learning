import request from './request.js'

export function getTodayReviews() {
  return request.get('/reviews/today')
}

export function submitReviewResult(questionId, rating) {
  return request.post(`/reviews/${questionId}/result`, { rating })
}
