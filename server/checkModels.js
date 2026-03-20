require('dotenv').config()
const { GoogleGenerativeAI } = require('@google/generative-ai')

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY)

async function check() {
  console.log('Fetching available models...')
  const models = await genAI.listModels()
  for (const model of models.models) {
    if (model.supportedGenerationMethods.includes('generateContent')) {
      console.log(model.name)
    }
  }
}

check().catch(console.error)