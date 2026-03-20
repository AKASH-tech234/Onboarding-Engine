require('dotenv').config()
const { GoogleGenerativeAI } = require('@google/generative-ai')

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY)

async function complete(systemPrompt, userPrompt) {
  const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' })
  const result = await model.generateContent(systemPrompt + '\n\n' + userPrompt)
  const text = result.response.text()
  return text.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim()
}

async function embed(text) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key=${process.env.GEMINI_API_KEY}`
  
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content: { parts: [{ text }] },
      outputDimensionality: 768
    })
  })

  const data = await response.json()
  
  if (!response.ok) {
    throw new Error(`Embed failed: ${data.error?.message || response.statusText}`)
  }

  return data.embedding.values
}

module.exports = { complete, embed }