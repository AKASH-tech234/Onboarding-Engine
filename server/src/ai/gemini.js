const { GoogleGenerativeAI } = require('@google/generative-ai')
require('dotenv').config()

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY)

async function complete(systemPrompt, userPrompt) {
  const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' })
  const result = await model.generateContent(systemPrompt + '\n\n' + userPrompt)
  const text = result.response.text()
  return text.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim()
}

async function embed(text) {
  const model = genAI.getGenerativeModel({ model: 'text-embedding-004' })
  const result = await model.embedContent(text)
  return result.embedding.values
}

module.exports = { complete, embed }