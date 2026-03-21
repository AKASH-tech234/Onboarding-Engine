const localApiUrl = 'http://localhost:3001/api/v1'

export function getApiBaseUrl() {
  const envUrl = import.meta.env.VITE_API_URL?.trim()

  if (envUrl) {
    return envUrl.replace(/\/+$/, '')
  }

  if (import.meta.env.DEV) {
    return localApiUrl
  }

  return '/api/v1'
}
