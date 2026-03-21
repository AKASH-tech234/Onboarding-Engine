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
  const pdfParseModule = require('pdf-parse')

  if (typeof pdfParseModule === 'function') {
    const result = await pdfParseModule(buffer)
    return result.text
  }

  if (typeof pdfParseModule.default === 'function') {
    const result = await pdfParseModule.default(buffer)
    return result.text
  }

  if (pdfParseModule.PDFParse) {
    const parser = new pdfParseModule.PDFParse({ verbosity: 0, data: buffer })

    try {
      const result = await parser.getText()
      return result.text
    } finally {
      await parser.destroy()
    }
  }

  throw new Error('PDF_PARSE_UNAVAILABLE')
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
  let recognizedFormat = false

  if (PDF_MIME_TYPES.has(normalizedMimetype) || extension === '.pdf' || looksLikePdf(buffer)) {
    recognizedFormat = true
    try {
      text = await extractPdfText(buffer)
      parsed = true
    } catch (error) {
      if (extension !== '.docx' && !looksLikeZip(buffer)) {
        throw new Error('TEXT_EXTRACTION_FAILED')
      }
    }
  }

  if (!parsed && (DOCX_MIME_TYPES.has(normalizedMimetype) || extension === '.docx' || looksLikeZip(buffer))) {
    recognizedFormat = true
    try {
      text = await extractDocxText(buffer)
      parsed = true
    } catch (error) {
      throw new Error('TEXT_EXTRACTION_FAILED')
    }
  }

  if (!parsed) {
    if (recognizedFormat) {
      throw new Error('TEXT_EXTRACTION_FAILED')
    }
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
