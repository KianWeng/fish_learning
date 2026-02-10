/**
 * 科目常量与科目图标（单字图标：语数英物化生政史地科）
 */

/** 常见科目（用于下拉框、筛选、图标判断）；含「科学」，选非预设用「自定义」 */
export const COMMON_COURSES = ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治', '科学']

/** 下拉框中「自定义」选项的文案，选后用户输入的内容会作为 course 存储 */
export const CUSTOM_COURSE_LABEL = '自定义'

/** 新建/编辑错题本时的科目下拉选项：常见科目 + 自定义 */
export const COURSE_PICKER_OPTIONS = [...COMMON_COURSES, CUSTOM_COURSE_LABEL]

/** 判断是否为「常见科目」（用于显示预设图标，否则用默认图标） */
export function isCommonCourse(course) {
  if (!course || typeof course !== 'string') return false
  return COMMON_COURSES.includes(course.trim())
}

const ICON_COLOR = '#4A90E2'
/** 科目名 → 单字（图标用） */
const COURSE_CHAR = {
  语文: '语',
  数学: '数',
  英语: '英',
  物理: '物',
  化学: '化',
  生物: '生',
  历史: '史',
  地理: '地',
  政治: '政',
  科学: '科',
  其他: '其'
}

function buildCharSvg(char) {
  return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><text x="12" y="17" text-anchor="middle" font-size="14" font-weight="600" fill="C" font-family="sans-serif">' + char + '</text></svg>'
}

/**
 * 根据科目名返回单字图标的 data URI，用于 <image :src="..." />
 * @param {string} course - 科目名（语文/数学/…/科学 或自定义字符串）
 */
export function getCourseIconDataUri(course) {
  const key = (course && course.trim()) || '其他'
  const char = COURSE_CHAR[key] || COURSE_CHAR['其他']
  const svg = buildCharSvg(char).replace(/C/g, ICON_COLOR)
  return 'data:image/svg+xml,' + encodeURIComponent(svg)
}
