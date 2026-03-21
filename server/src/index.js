const path = require('path')
require('dotenv').config({ path: path.resolve(__dirname, '../.env') })

const express = require('express')
const cors = require('cors')

const app = express()

function getAllowedOrigins() {
  return (process.env.CORS_ORIGINS || '')
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean)
}

function buildCorsOptions() {
  const allowedOrigins = getAllowedOrigins()

  return {
    origin(origin, callback) {
      if (!origin) {
        return callback(null, true)
      }

      if (allowedOrigins.length === 0 || allowedOrigins.includes(origin)) {
        return callback(null, true)
      }

      return callback(new Error(`CORS blocked for origin: ${origin}`))
    },
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'x-seed-secret'],
    optionsSuccessStatus: 200,
  }
}

const corsOptions = buildCorsOptions()

app.use(cors(corsOptions))
app.options(/.*/, cors(corsOptions))
app.use(express.json())
app.use(express.urlencoded({ extended: true }))

app.get('/', (req, res) => {
  res.json({ status: 'ok', service: 'onboarding-engine-api' })
})

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
})

const sessionsRouter = require('./routes/sessions')
app.use('/api/v1/sessions', sessionsRouter)

const coursesRouter = require('./routes/courses')
app.use('/api/v1/courses', coursesRouter)

const skillsRouter = require('./routes/skills')
app.use('/api/v1/skills', skillsRouter)

if (process.env.EXPRESS_STATIC === 'true') {
  app.use(express.static(path.join(__dirname, '../public')))
}

app.use((err, req, res, next) => {
  console.error(err.stack)

  const status = err.message?.startsWith('CORS blocked') ? 403 : (err.status || 500)
  res.status(status).json({ error: err.message || 'Internal server error' })
})

if (require.main === module) {
  const port = Number(process.env.PORT) || 8080
  app.listen(port, '0.0.0.0', () => console.log(`Server running on port ${port}`))
}

module.exports = { app }
