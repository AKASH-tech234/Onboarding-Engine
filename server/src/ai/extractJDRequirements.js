const { z } = require('zod');
const { complete } = require('./gemini.js');
const { withRetry } = require('../utils/retry.js');

const jdResponseSchema = z.object({
  job_title: z.string().nullable(),
  department: z.string().nullable(),
  seniority_level: z.string().nullable(),
  skills: z.array(z.object({
    name: z.string(),
    level: z.enum(['beginner','intermediate','advanced']),
    required: z.boolean(),
    context: z.string()
  }))
});

async function extractJDRequirements(jdText) {
  const systemPrompt = "You are a precise job requirements extraction engine. Extract ONLY skills and competencies explicitly stated in the job description. Return ONLY valid JSON, no markdown, no explanation.";

  const userPrompt = `
Extract all required and preferred skills from this job description. For each skill return:
- name: canonical skill name
- level: minimum required level ["beginner","intermediate","advanced"]
- required: true if mandatory, false if preferred
- context: exact phrase from JD

Return format:
{"job_title":string|null,"department":string|null,"seniority_level":string|null,"skills":[{"name":string,"level":string,"required":boolean,"context":string}]}

Job Description:
${jdText}
`;

  return withRetry(async () => {
    const jsonString = await complete(systemPrompt, userPrompt);
    let parsed;
    try {
      parsed = JSON.parse(jsonString);
    } catch (e) {
      throw new Error('LLM_JSON_INVALID');
    }
    return jdResponseSchema.parse(parsed);
  });
}

module.exports = { extractJDRequirements };
