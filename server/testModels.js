require('dotenv').config()
const { GoogleGenerativeAI } = require('@google/generative-ai')
const fs = require('fs')

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY)

const modelsToTest = [
  'gemini-2.0-flash',
  'gemini-2.5-flash',
  'gemini-1.5-flash',
  'gemini-pro',
  'gemini-2.5-pro'
]

async function testModels() {
  const results = {}
  for (const modelName of modelsToTest) {
    try {
      const model = genAI.getGenerativeModel({ model: modelName })
      const result = await model.generateContent('Say Hi')
      results[modelName] = 'SUCCESS'
    } catch (e) {
      results[modelName] = `FAILED: ${e.message.split('\n')[0]}`
    }
  }
  fs.writeFileSync('model_test_results.json', JSON.stringify(results, null, 2))
}

testModels().catch(console.error)
