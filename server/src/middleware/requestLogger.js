const logger = require('../utils/logger')

function requestLogger(req, res, next) {
  const start = Date.now()

  res.on('finish', () => {
    const duration = Date.now() - start
    const message = `${req.method} ${req.originalUrl} ${res.statusCode} ${duration}ms`
    if (res.statusCode >= 500) {
      logger.error(message)
    } else if (res.statusCode >= 400) {
      logger.warn(message)
    } else {
      logger.http(message)
    }
  })

  next()
}

module.exports = requestLogger
