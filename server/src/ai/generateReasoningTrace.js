const { complete } = require('./gemini')
const { withRetry } = require('../utils/retry')

async function generateReasoningTrace({ extractedSkills, requiredSkills, skillGap, pathway }) {
  const system = `You are an expert L&D advisor. Write a clear reasoning trace explaining WHY each recommendation was made. Be specific, cite the skill gap, and explain the course selection logic. No hallucinations — only reference data provided to you.`

  const user = `Given this onboarding analysis, explain each recommendation:

Candidate Profile: ${JSON.stringify(extractedSkills)}
Job Requirements: ${JSON.stringify(requiredSkills)}
Skill Gaps: ${JSON.stringify(skillGap)}
Recommended Pathway: ${JSON.stringify(pathway)}

Write a reasoning trace with these exact sections:
1. Candidate Assessment (2-3 sentences on the candidate's current profile)
2. Gap Identification (one bullet per gap: skill name, severity, why it matters)
3. Course Selection Rationale (one bullet per course: why this course for this gap)
4. Pathway Ordering Logic (why the sequence is ordered this way)
5. Estimated Time to Competency (sum durations, state total hrs and realistic timeline)`

  const raw = await withRetry(() => complete(system, user))

  const sections = {
    candidate_assessment: '',
    gap_identification: '',
    course_selection_rationale: '',
    pathway_ordering_logic: '',
    estimated_time_to_competency: '',
    raw
  }

  try {
    const parts = raw.split(/\n(?=\d\.)/g)
    for (const part of parts) {
      if (part.startsWith('1.')) sections.candidate_assessment = part.replace(/^1\.\s*[^\n]*\n?/, '').trim()
      else if (part.startsWith('2.')) sections.gap_identification = part.replace(/^2\.\s*[^\n]*\n?/, '').trim()
      else if (part.startsWith('3.')) sections.course_selection_rationale = part.replace(/^3\.\s*[^\n]*\n?/, '').trim()
      else if (part.startsWith('4.')) sections.pathway_ordering_logic = part.replace(/^4\.\s*[^\n]*\n?/, '').trim()
      else if (part.startsWith('5.')) sections.estimated_time_to_competency = part.replace(/^5\.\s*[^\n]*\n?/, '').trim()
    }
  } catch {
    // parsing failed, raw is still available as fallback
  }

  return sections
}

module.exports = { generateReasoningTrace }