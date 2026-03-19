//for connecting to the ML service and handling all ML-related logic to keep server.js clean and focused on routing and middleware. This module abstracts away the details of communicating with the ML service, including error handling and response parsing.
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:5001';
const TIMEOUT_MS = 120000;

const mlClient = axios.create({
  baseURL: ML_SERVICE_URL,
  timeout: TIMEOUT_MS,
  headers: { 'Content-Type': 'application/json' }
});

async function checkMLServiceHealth() {
  try {
    const res = await mlClient.get('/health');
    return res.data.status === 'ok';
  } catch {
    return false;
  }
}

async function extractTextFromPDF(filePath) {
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));

  const res = await mlClient.post('/extract-text', form, {
    headers: { ...form.getHeaders() },
    timeout: 30000
  });

  if (!res.data.text) {
    throw new Error('PDF text extraction returned empty result');
  }
  return res.data.text;
}

async function runFullAnalysis(resumeText, jdText) {
  const res = await mlClient.post('/analyze', {
    resume_text: resumeText,
    jd_text: jdText
  });

  if (!res.data.success) {
    throw new Error(res.data.error || 'ML analysis returned an error');
  }
  return res.data;
}

async function runAnalysisWithFiles(resumeFilePath, jdFilePath = null, jdText = null) {
  const isHealthy = await checkMLServiceHealth();
  if (!isHealthy) {
    throw new Error('ML service is unavailable. Please try again shortly.');
  }

  const resumeText = await extractTextFromPDF(resumeFilePath);
  let jobDescriptionText = jdText;

  if (jdFilePath) {
    jobDescriptionText = await extractTextFromPDF(jdFilePath);
  }

  if (!jobDescriptionText || jobDescriptionText.trim().length < 50) {
    throw new Error('Job description is too short or could not be extracted.');
  }
  if (!resumeText || resumeText.trim().length < 50) {
    throw new Error('Resume is too short or could not be extracted. Ensure the PDF is not scanned/image-only.');
  }

  return await runFullAnalysis(resumeText, jobDescriptionText);
}

module.exports = { runAnalysisWithFiles, checkMLServiceHealth };