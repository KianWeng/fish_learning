/**
 * 图片本地缓存：远程 URL 下载后存到本地，下次直接用本地路径，减轻服务器压力。
 *
 * 是否使用缓存 / 后端是否收到 GET：
 * - 小程序：会走本地文件缓存。第一次显示某张图会下载并保存，后端收到 GET；之后同一张图
 *   直接读本地路径，控制台会打 [image-cache] 命中本地缓存，后端不再收到该图的 GET。
 * - H5（浏览器）：不做本地文件缓存，始终返回远程 URL，每次显示图片都会由浏览器发请求，
 *   所以后端会收到 GET。减少请求只能靠后端对 /files/ 返回 Cache-Control，由浏览器做 HTTP 缓存。
 *
 * - 小程序：getFileSystemManager().saveFile 持久化，storage 记录 URL -> 本地路径
 * - H5：直接返回远程 URL
 */

const CACHE_PREFIX = 'img_'
const MAX_CACHE_KEYS = 500

/** 当前是否为 H5：H5 不做本地文件缓存。微信/支付宝等小程序必须判为 false，走本地缓存 */
function isH5() {
  if (typeof uni === 'undefined') return true
  try {
    const info = uni.getSystemInfoSync && uni.getSystemInfoSync()
    if (!info) return true
    const up = String(info.uniPlatform || '').toLowerCase()
    const pl = String(info.platform || '').toLowerCase()
    if (up.startsWith('mp-') || pl.startsWith('mp-') || up === 'miniprogram') return false
    return up === 'h5' || pl === 'h5'
  } catch (e) {
    return false
  }
}

function hashUrl(url) {
  let h = 0
  const s = String(url)
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h) + s.charCodeAt(i) | 0
  }
  return (h >>> 0).toString(36)
}

function getStorageKey(url) {
  return CACHE_PREFIX + hashUrl(url)
}

/** 是否支持本地文件持久化（微信等小程序） */
function canSaveFile() {
  if (typeof uni === 'undefined') return false
  try {
    const fs = uni.getFileSystemManager && uni.getFileSystemManager()
    return fs && typeof fs.saveFile === 'function'
  } catch (e) {
    return false
  }
}

/** 检查本地文件是否仍存在 */
function isFileAccessible(filePath) {
  try {
    const fs = uni.getFileSystemManager && uni.getFileSystemManager()
    if (!fs || typeof fs.accessSync !== 'function') return true
    fs.accessSync(filePath)
    return true
  } catch (e) {
    return false
  }
}

/** 清理过期缓存键（简单 FIFO：只保留最近 MAX_CACHE_KEYS 个 key 的映射，避免 storage 爆满，此处仅按 key 数量限制，不做时间淘汰） */
function pruneCacheKeys() {
  try {
    const keys = []
    const prefix = CACHE_PREFIX
    // uni.getStorageInfoSync 可得到所有 key，筛选出 img_ 开头的
    const info = uni.getStorageInfoSync()
    if (info && info.keys) {
      keys.push(...info.keys.filter(k => k.startsWith(prefix)))
    }
    if (keys.length <= MAX_CACHE_KEYS) return
    // 简单策略：删掉前 N 个（按 key 排序后删最早的）
    keys.sort()
    const toRemove = keys.slice(0, keys.length - MAX_CACHE_KEYS)
    toRemove.forEach(k => {
      try { uni.removeStorageSync(k) } catch (e) {}
    })
  } catch (e) {}
}

/**
 * 获取可用的图片地址：若已缓存则返回本地路径，否则下载并缓存后返回。
 * @param {string} remoteUrl - 完整远程图片 URL（或 data URL）
 * @returns {Promise<string>} 最终用于 <image src=""> 的地址（本地路径或远程 URL 或 data URL）
 */
export function getCachedImageUrl(remoteUrl) {
  if (!remoteUrl || typeof remoteUrl !== 'string') {
    return Promise.resolve(remoteUrl || '')
  }
  if (remoteUrl.startsWith('data:')) {
    return Promise.resolve(remoteUrl)
  }
  if (isH5()) {
    return Promise.resolve(remoteUrl)
  }

  const key = getStorageKey(remoteUrl)

  if (canSaveFile()) {
    try {
      const saved = uni.getStorageSync(key)
      if (saved && typeof saved === 'string' && isFileAccessible(saved)) {
        if (typeof console !== 'undefined' && console.log) {
          console.log('[image-cache] 命中本地缓存，未请求服务器', remoteUrl.slice(-50))
        }
        return Promise.resolve(saved)
      }
      if (saved) uni.removeStorageSync(key)
    } catch (e) {}
  }

  if (typeof console !== 'undefined' && console.log) {
    console.log('[image-cache] 未命中，将下载并缓存', remoteUrl.slice(-55))
  }
  return new Promise((resolve) => {
    uni.downloadFile({
      url: remoteUrl,
      success: (res) => {
        if (res.statusCode !== 200 || !res.tempFilePath) {
          resolve(remoteUrl)
          return
        }
        const tempFilePath = res.tempFilePath
        if (canSaveFile()) {
          try {
            const fs = uni.getFileSystemManager()
            fs.saveFile({
              tempFilePath,
              success: (saveRes) => {
                if (saveRes.savedFilePath) {
                  try {
                    uni.setStorageSync(key, saveRes.savedFilePath)
                    pruneCacheKeys()
                    if (typeof console !== 'undefined' && console.log) {
                      console.log('[image-cache] 已写入本地缓存', remoteUrl.slice(-55))
                    }
                    resolve(saveRes.savedFilePath)
                  } catch (e) {
                    if (typeof console !== 'undefined' && console.warn) {
                      console.warn('[image-cache] setStorageSync 失败', e)
                    }
                    resolve(remoteUrl)
                  }
                } else {
                  resolve(remoteUrl)
                }
              },
              fail: (err) => {
                if (typeof console !== 'undefined' && console.warn) {
                  console.warn('[image-cache] saveFile 失败', err && (err.errMsg || err))
                }
                resolve(remoteUrl)
              }
            })
          } catch (e) {
            if (typeof console !== 'undefined' && console.warn) {
              console.warn('[image-cache] saveFile 调用异常', e)
            }
            resolve(remoteUrl)
          }
        } else {
          resolve(tempFilePath || remoteUrl)
        }
      },
      fail: () => resolve(remoteUrl)
    })
  })
}

/**
 * 使某 URL 的缓存失效（例如用户更换了封面/头像后调用，下次会重新下载）
 */
export function invalidateImageCache(remoteUrl) {
  if (!remoteUrl || typeof remoteUrl !== 'string') return
  try {
    uni.removeStorageSync(getStorageKey(remoteUrl))
  } catch (e) {}
}
