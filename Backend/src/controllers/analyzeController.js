const fs = require('fs');
const { runAnalysisWithFiles } = require('../services/mlService');

function cleanupFiles(...paths) {
  paths.forEach(p => {
    if (p && fs.existsSync(p)) {
      try { fs.unlinkSync(p); } catch {}
    }
  });
}

async function analyzeHandler(req, res, next) {
  const resumeFile = req.files?.resume?.[0];
  const jdFile = req.files?.job_description?.[0];
  const jdText = req.body?.jd_text;

  if (!resumeFile) {
    return res.status(400).json({ error: 'Resume PDF is required.' });
  }
  if (!jdFile && (!jdText || jdText.trim().length < 50)) {
    cleanupFiles(resumeFile?.path);
    return res.status(400).json({ error: 'A Job Description PDF or text (min 50 chars) is required.' });
  }

  const resumePath = resumeFile.path;
  const jdPath = jdFile?.path || null;

  try {
    console.log(`[ANALYZE] Resume: ${resumeFile.originalname}, JD: ${jdFile?.originalname || 'text input'}`);
    const startTime = Date.now();

    const result = await runAnalysisWithFiles(resumePath, jdPath, jdText);

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log(`[ANALYZE] Completed in ${duration}s`);

    res.json({
      ...result,
      meta: {
        processing_time_seconds: parseFloat(duration),
        resume_filename: resumeFile.originalname,
        jd_filename: jdFile?.originalname || 'text-input'
      }
    });
  } catch (err) {
    console.error('[ANALYZE ERROR]', err.message);
    next(err);
  } finally {
    cleanupFiles(resumePath, jdPath);
  }
}

async function sampleHandler(req, res, next) {
  try {
    const samplePath = require('path').join(__dirname, '../data/sample_result.json');
    if (fs.existsSync(samplePath)) {
      const sample = JSON.parse(fs.readFileSync(samplePath, 'utf8'));
      return res.json({ ...sample, meta: { is_sample: true } });
    }
    res.status(404).json({ error: 'Sample data not available.' });
  } catch (err) {
    next(err);
  }
}

module.exports = { analyzeHandler, sampleHandler };