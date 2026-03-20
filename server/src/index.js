const path = require('path');
const express = require('express');
const cors = require('cors');
const multer = require('multer');

const app = express();

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 },
});

function loadRoute(modulePath) {
  try {
    return require(modulePath);
  } catch (error) {
    if (error.code === 'MODULE_NOT_FOUND') {
      const router = express.Router();
      return router;
    }
    throw error;
  }
}

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.use('/api/v1/sessions', loadRoute('./routes/sessions'));
app.use('/api/v1/courses', loadRoute('./routes/courses'));
app.use('/api/v1/skills', loadRoute('./routes/skills'));

if (process.env.EXPRESS_STATIC === 'true') {
  app.use(express.static(path.join(__dirname, '../public')));
}

app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(err.status || 500).json({ error: err.message || 'Internal server error' });
});

if (require.main === module) {
  const port = process.env.PORT || 3001;
  app.listen(port, () => {
    console.log('Server running on port', port);
  });
}

module.exports = { app, upload };
