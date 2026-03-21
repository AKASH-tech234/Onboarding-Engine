const path = require('path')
const mammoth = require('mammoth')

const PDF_MIME_TYPES = new Set([
  'application/pdf',
  'application/x-pdf',
  'application/acrobat',
  'applications/vnd.pdf',
  'text/pdf',
  'text/x-pdf',
])

const DOCX_MIME_TYPES = new Set([
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/octet-stream',
  'application/zip',
])

function getFileExtension(originalname = '') {
  return path.extname(originalname).toLowerCase()
}

function looksLikePdf(buffer) {
  return buffer?.subarray(0, 5).toString() === '%PDF-'
}

function looksLikeZip(buffer) {
  return buffer?.subarray(0, 2).toString() === 'PK'
}

async function extractPdfText(buffer) {
  const { PDFParse } = require('pdf-parse')
  const parser = new PDFParse({ verbosity: 0, data: buffer })
  const result = await parser.getText()
  return result.text
}

async function extractDocxText(buffer) {
  const result = await mammoth.extractRawText({ buffer })
  return result.value
}

async function extractText({ buffer, mimetype, originalname }) {
  const normalizedMimetype = (mimetype || '').toLowerCase()
  const extension = getFileExtension(originalname)
  let text = ''
  let parsed = false

  if (PDF_MIME_TYPES.has(normalizedMimetype) || extension === '.pdf' || looksLikePdf(buffer)) {
    try {
      text = await extractPdfText(buffer)
      parsed = true
    } catch (error) {
      if (extension !== '.docx' && !looksLikeZip(buffer)) {
        throw error
      }
    }
  }

  if (!parsed && (DOCX_MIME_TYPES.has(normalizedMimetype) || extension === '.docx' || looksLikeZip(buffer))) {
    text = await extractDocxText(buffer)
    parsed = true
  }

  if (!parsed) {
    throw new Error('UNSUPPORTED_FORMAT')
  }

  text = text.replace(/\u0000/g, '').replace(/\n{3,}/g, '\n\n').trim()

  const wordCount = text.split(/\s+/).filter(Boolean).length

  if (wordCount < 80) {
    throw new Error('SCANNED_PDF')
  }

  return { text, wordCount }
}

module.exports = { extractText }
