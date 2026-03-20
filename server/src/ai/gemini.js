require('dotenv').config()
const { GoogleGenerativeAI } = require('@google/generative-ai')
const Groq = require('groq-sdk')

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY)
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY })

async function complete(systemPrompt, userPrompt) {
  const isJson = systemPrompt.toLowerCase().includes('json') || userPrompt.toLowerCase().includes('json')
  
  const completion = await groq.chat.completions.create({
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: userPrompt }
    ],
    model: "llama-3.3-70b-versatile",
    response_format: isJson ? { type: "json_object" } : undefined
  })
  
  const text = completion.choices[0].message.content
  return text.trim()
}

async function* stream(systemPrompt, userPrompt) {
  const stream = await groq.chat.completions.create({
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: userPrompt }
    ],
    model: "llama-3.3-70b-versatile",
    stream: true
  })
  
  for await (const chunk of stream) {
    yield chunk.choices[0]?.delta?.content || ""
  }
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

module.exports = { complete, stream, embed }