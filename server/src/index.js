const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');

const sessionsRouter = require('./routes/sessions.js');
const coursesRouter = require('./routes/courses.js');
const skillsRouter = require('./routes/skills.js');

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const upload = multer({ 
  storage: multer.memoryStorage(), 
  limits: { fileSize: 10 * 1024 * 1024 } 
});

app.get('/api/v1/health', (req, res) => res.json({ status: 'ok', timestamp: new Date().toISOString() }));

app.use('/api/v1/sessions', sessionsRouter);
app.use('/api/v1/courses', coursesRouter);
app.use('/api/v1/skills', skillsRouter);

app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(err.status || 500).json({ error: err.message || 'Internal server error' });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = { upload };
