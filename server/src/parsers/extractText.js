const mammoth = require('mammoth')

async function extractText({ buffer, mimetype }) {
  let text = ''

 if (mimetype === 'application/pdf') {
  const { PDFParse } = require('pdf-parse')
  const parser = new PDFParse({ verbosity: 0, data: buffer })
  const result = await parser.getText()
  text = result.text
} else if (mimetype === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
    const result = await mammoth.extractRawText({ buffer })
    text = result.value
  } else {
    throw new Error('UNSUPPORTED_FORMAT')
  }

  text = text.replace(/\n{3,}/g, '\n\n').trim()

  const wordCount = text.split(/\s+/).filter(Boolean).length

  if (wordCount < 50) {
    throw new Error('SCANNED_PDF')
  }

  return { text, wordCount }
}

module.exports = { extractText }