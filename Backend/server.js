require('dotenv').config();
const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const path = require('path');
const fs = require('fs');

const analyzeRoutes = require('./src/routes/analyze');
const catalogRoutes = require('./src/routes/catalog');

const app = express();
const PORT = process.env.PORT || 3001;

const uploadDir = process.env.UPLOAD_DIR || './uploads';
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

app.use(cors({
  origin: process.env.NODE_ENV === 'production'
    ? process.env.FRONTEND_URL
    : ['http://localhost:3000', 'http://localhost:5173'],
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 50,
  message: { error: 'Too many requests, please try again later.' }
});
app.use('/api/', limiter);

app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'backend',
    timestamp: new Date().toISOString(),
    ml_service_url: process.env.ML_SERVICE_URL
  });
});

app.use('/api/analyze', analyzeRoutes);
app.use('/api/catalog', catalogRoutes);

app.use((err, req, res, next) => {
  console.error('[ERROR]', err.stack);
  if (err.code === 'LIMIT_FILE_SIZE') {
    return res.status(413).json({ error: `File too large. Max ${process.env.MAX_FILE_SIZE_MB || 10}MB allowed.` });
  }
  res.status(err.status || 500).json({
    error: err.message || 'Internal server error'
  });
});

app.use((req, res) => {
  res.status(404).json({ error: `Route ${req.method} ${req.path} not found` });
});

app.listen(PORT, () => {
  console.log(`\n Backend running on http://localhost:${PORT}`);
  console.log(` ML Service:   ${process.env.ML_SERVICE_URL || 'http://localhost:5001'}`);
  console.log(` Environment:  ${process.env.NODE_ENV || 'development'}\n`);
});

module.exports = app;