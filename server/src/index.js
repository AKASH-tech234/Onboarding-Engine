const path = require('path')
const express = require('express')
const cors = require('cors')

const app = express()

app.use(cors())
app.use(express.json())
app.use(express.urlencoded({ extended: true }))

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
})

// --- REMOVE loadRoute AND USE STANDARD REQUIRES ---
// If any of these fail, the server will crash and tell you EXACTLY why in the Railway logs.

const sessionsRouter = require('./routes/sessions');
app.use('/api/v1/sessions', sessionsRouter);

const coursesRouter = require('./routes/courses');
app.use('/api/v1/courses', coursesRouter);

const skillsRouter = require('./routes/skills');
app.use('/api/v1/skills', skillsRouter);

// --------------------------------------------------

if (process.env.EXPRESS_STATIC === 'true') {
  app.use(express.static(path.join(__dirname, '../public')))
}

app.use((err, req, res, next) => {
  console.error(err.stack)
  res.status(err.status || 500).json({ error: err.message || 'Internal server error' })
})

if (require.main === module) {
  const port = process.env.PORT || 8080
  app.listen(port, '0.0.0.0', () => console.log('Server running on port', port))
}

module.exports = { app }