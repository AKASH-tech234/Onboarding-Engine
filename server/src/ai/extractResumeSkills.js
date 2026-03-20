const { z } = require('zod');
const { complete } = require('./gemini.js');
const { withRetry } = require('../utils/retry.js');

const resumeResponseSchema = z.object({
  candidate_name: z.string().nullable(),
  total_experience_years: z.number().nullable(),
  current_role: z.string().nullable(),
  skills: z.array(z.object({
    name: z.string(),
    level: z.enum(['beginner','intermediate','advanced']),
    years: z.number().nullable(),
    evidence: z.string()
  }))
});

async function extractResumeSkills(resumeText) {
  const systemPrompt = "You are a precise HR data extraction engine. Extract ONLY skills explicitly mentioned or clearly implied by the resume text. Do NOT infer skills not evidenced in the text. Return ONLY valid JSON, no markdown, no explanation.";

  const userPrompt = `
Extract all skills from this resume. For each skill return:
- name: canonical skill name (e.g. "React" not "ReactJS")
- level: one of ["beginner","intermediate","advanced"] inferred from context
- years: numeric years or null
- evidence: one sentence from resume supporting this skill

Return format:
{"candidate_name":string|null,"total_experience_years":number|null,"current_role":string|null,"skills":[{"name":string,"level":string,"years":number|null,"evidence":string}]}

Resume:
${resumeText}
`;

  return withRetry(async () => {
    const jsonString = await complete(systemPrompt, userPrompt);
    let parsed;
    try {
      parsed = JSON.parse(jsonString);
    } catch (e) {
      throw new Error('LLM_JSON_INVALID');
    }
    
    return resumeResponseSchema.parse(parsed);
  });
}

module.exports = { extractResumeSkills };
