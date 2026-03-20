const assert = require('node:assert/strict')
const logger = require('../utils/logger')

function runLoggerTests() {
  // Logger should have the expected log-level methods
  assert.equal(typeof logger.info, 'function', 'logger.info should be a function')
  assert.equal(typeof logger.warn, 'function', 'logger.warn should be a function')
  assert.equal(typeof logger.error, 'function', 'logger.error should be a function')
  assert.equal(typeof logger.http, 'function', 'logger.http should be a function')
  assert.equal(typeof logger.debug, 'function', 'logger.debug should be a function')

  // Logger should have a valid log level set
  const validLevels = ['error', 'warn', 'info', 'http', 'verbose', 'debug', 'silly']
  assert.ok(validLevels.includes(logger.level), `logger.level "${logger.level}" should be a valid winston level`)

  // Logger should have at least one transport (console + file)
  assert.ok(logger.transports.length >= 1, 'logger should have at least one transport')

  // Calling log methods should not throw
  assert.doesNotThrow(() => logger.info('test info message'), 'logger.info should not throw')
  assert.doesNotThrow(() => logger.warn('test warn message'), 'logger.warn should not throw')
  assert.doesNotThrow(() => logger.error('test error message'), 'logger.error should not throw')
  assert.doesNotThrow(() => logger.http('test http message'), 'logger.http should not throw')
  assert.doesNotThrow(() => logger.debug('test debug message'), 'logger.debug should not throw')
  assert.doesNotThrow(() => logger.error(new Error('test error object')), 'logger.error should accept Error objects')
}

module.exports = { runLoggerTests }
