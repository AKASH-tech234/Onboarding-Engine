const { complete } = require('./gemini.js');
const { withRetry } = require('../utils/retry.js');

async function generateReasoningTrace({ extractedSkills, requiredSkills, skillGap, pathway }) {
  const systemPrompt = "You are an expert L&D advisor. Write a clear reasoning trace explaining WHY each recommendation was made. Cite specific skill gaps. Only reference data provided — never invent course names or skills.";
  
  const userPrompt = `
Given this onboarding analysis, explain each recommendation:

Candidate Profile:
${JSON.stringify(extractedSkills, null, 2)}

Job Requirements:
${JSON.stringify(requiredSkills, null, 2)}

Skill Gaps:
${JSON.stringify(skillGap, null, 2)}

Recommended Pathway:
${JSON.stringify(pathway, null, 2)}

Write a reasoning trace with these sections exactly numbered 1 to 5:
1. Candidate Assessment
2. Gap Identification
3. Course Selection Rationale
4. Pathway Ordering Logic
5. Estimated Time to Competency
`;

  return withRetry(async () => {
    const fullText = await complete(systemPrompt, userPrompt);
    
    // Split by numbered list headings
    const parts = fullText.split(/\n[1-5]\.\s/);
    if (parts.length < 6) {
      return { raw: fullText };
    }

    return {
      candidate_assessment: parts[1].trim(),
      gap_identification: parts[2].trim(),
      course_selection_rationale: parts[3].trim(),
      pathway_ordering_logic: parts[4].trim(),
      estimated_time_to_competency: parts[5].trim(),
      raw: fullText
    };
  });
}

module.exports = { generateReasoningTrace };
