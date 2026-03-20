async function withRetry(fn, maxAttempts = 2) {
  let lastError
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn()
    } catch (err) {
      lastError = err
      if (attempt < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }
  }
  throw lastError
}

module.exports = { withRetry }