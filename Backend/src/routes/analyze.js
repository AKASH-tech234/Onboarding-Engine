const express = require('express');
const router = express.Router();
const upload = require('../middleware/upload');
const { analyzeHandler, sampleHandler } = require('../controllers/analyzeController');

router.post(
  '/',
  upload.fields([
    { name: 'resume', maxCount: 1 },
    { name: 'job_description', maxCount: 1 }
  ]),
  analyzeHandler
);

router.get('/sample', sampleHandler);

module.exports = router;