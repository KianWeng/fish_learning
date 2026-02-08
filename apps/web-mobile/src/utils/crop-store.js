/**
 * 裁剪页与添加题页之间传递图片路径，仅用模块变量，避免使用 getApp()
 */
let sourcePath = ''
let resultPath = ''

export function setSourcePath(path) {
  sourcePath = path || ''
}

export function getSourcePath() {
  return sourcePath
}

export function setResultPath(path) {
  resultPath = path || ''
}

export function getResultPath() {
  return resultPath
}

export function clear() {
  sourcePath = ''
  resultPath = ''
}
