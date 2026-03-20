const express = require('express')
const supabase = require('../db/supabaseClient')
const upload = require('../middleware/upload')
const { extractText } = require('../parsers/extractText')
const { extractResumeSkills } = require('../ai/extractResumeSkills')
const { extractJDRequirements } = require('../ai/extractJDRequirements')
const { normalizeSkills } = require('../ai/normalizeSkills')
const { computeSkillGap } = require('../ai/computeSkillGap')
const { adaptivePathway } = require('../ai/adaptivePathway')
const { generateReasoningTrace, generateReasoningTraceStream } = require('../ai/generateReasoningTrace')

const router = express.Router()

router.post('/analyze', upload.fields([{ name: 'resume', maxCount: 1 }, { name: 'jd', maxCount: 1 }]), async (req, res, next) => {
  res.setHeader('Content-Type', 'text/event-stream')
  res.setHeader('Cache-Control', 'no-cache')
  res.setHeader('Connection', 'keep-alive')

  const sendEvent = (event, data) => res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
  const sendError = (msg, status = 400) => {
    sendEvent('error', { error: msg, status })
    res.end()
  }

  try {
    if (!req.files?.resume) return sendError('Resume file is required')
    if (!req.files?.jd && !req.body.jd_text) return sendError('Job description is required')

    sendEvent('status', { message: 'Extracting text from documents...' })

    let resumeText, jdText
    try {
      const result = await extractText({ buffer: req.files.resume[0].buffer, mimetype: req.files.resume[0].mimetype })
      resumeText = result.text
    } catch (e) {
      return sendError(e.message === 'SCANNED_PDF' ? 'Resume is too short or does not appear to be a real resume. Please upload a proper resume PDF.' : 'Resume format not supported.')
    }

    if (req.body.jd_text) {
      jdText = req.body.jd_text
    } else {
      try {
        const result = await extractText({ buffer: req.files.jd[0].buffer, mimetype: req.files.jd[0].mimetype })
        jdText = result.text
      } catch (e) {
        return sendError(e.message === 'SCANNED_PDF' ? 'Job description appears to be a scanned image. Please upload a text-based PDF.' : 'Unsupported format for JD.')
      }
    }

    sendEvent('status', { message: 'Analyzing candidate profile and job requirements concurrently...' })

    let resumeResult, jdResult
    try {
      [resumeResult, jdResult] = await Promise.all([
        extractResumeSkills(resumeText),
        extractJDRequirements(jdText)
      ])
    } catch (e) {
      if (e.message === 'LLM_JSON_INVALID') return sendError('Could not process skills with AI. Please try again.', 422)
      throw e
    }

    console.log('resumeResult.skills:', resumeResult.skills?.length, 'jdResult.skills:', jdResult.skills?.length)

    if (!resumeResult.skills || resumeResult.skills.length === 0) {
      return sendError('No skills could be extracted from the resume. Please upload a real resume.')
    }
    if (!jdResult.skills || jdResult.skills.length === 0) {
      return sendError('No requirements could be extracted from the job description. Please upload a real JD.')
    }

    sendEvent('status', { message: 'Searching database for matched skills...' })

    const allSkillNames = [...resumeResult.skills.map(s => s.name), ...jdResult.skills.map(s => s.name)]
    const normResults = await normalizeSkills(allSkillNames)
    const normMap = Object.fromEntries(normResults.map(r => [r.original, r]))

    resumeResult.skills = resumeResult.skills.map(s => ({ ...s, normalized_id: normMap[s.name]?.normalized_id }))
    jdResult.skills = jdResult.skills.map(s => ({ ...s, normalized_id: normMap[s.name]?.normalized_id }))

    sendEvent('status', { message: 'Computing skill gaps and generating pathway...' })

    const skillGap = computeSkillGap(resumeResult.skills, jdResult.skills)
    const pathwayResult = await adaptivePathway(skillGap, supabase)

    sendEvent('status', { message: 'Writing reasoning trace...' })

    const partialResponse = {
      candidate: { name: resumeResult.candidate_name, current_role: resumeResult.current_role, total_experience_years: resumeResult.total_experience_years },
      job_title: jdResult.job_title,
      skill_gap_summary: { total_gaps: skillGap.total_gaps, critical_gaps: skillGap.critical_gaps, already_met: skillGap.alreadyMet.length },
      pathway: pathwayResult,
      total_training_hrs: pathwayResult.total_training_hrs
    }
    sendEvent('pathway_ready', partialResponse)

    let fullTrace = ''
    const traceStream = generateReasoningTraceStream({
      extractedSkills: resumeResult.skills,
      requiredSkills: jdResult.skills,
      skillGap,
      pathway: pathwayResult
    })

    for await (const chunk of traceStream) {
      fullTrace += chunk
      sendEvent('trace_chunk', chunk)
    }

    sendEvent('status', { message: 'Saving session...' })

    const sections = { candidate_assessment: '', gap_identification: '', course_selection_rationale: '', pathway_ordering_logic: '', estimated_time_to_competency: '', raw: fullTrace }
    try {
      const parts = fullTrace.split(/\n(?=\d\.)/g)
      for (const part of parts) {
        if (part.startsWith('1.')) sections.candidate_assessment = part.replace(/^1\.\s*[^\n]*\n?/, '').trim()
        else if (part.startsWith('2.')) sections.gap_identification = part.replace(/^2\.\s*[^\n]*\n?/, '').trim()
        else if (part.startsWith('3.')) sections.course_selection_rationale = part.replace(/^3\.\s*[^\n]*\n?/, '').trim()
        else if (part.startsWith('4.')) sections.pathway_ordering_logic = part.replace(/^4\.\s*[^\n]*\n?/, '').trim()
        else if (part.startsWith('5.')) sections.estimated_time_to_competency = part.replace(/^5\.\s*[^\n]*\n?/, '').trim()
      }
    } catch {}

    const { data: sessionRow, error: dbError } = await supabase.from('sessions').insert({
      resume_text: resumeText, jd_text: jdText,
      extracted_skills: resumeResult, required_skills: jdResult,
      skill_gap: skillGap, pathway: pathwayResult, reasoning_trace: sections
    }).select('id').single()

    if (dbError) throw dbError

    partialResponse.session_id = sessionRow.id
    partialResponse.reasoning_trace = sections

    sendEvent('complete', partialResponse)
    res.end()

  } catch (err) {
    console.error('SSE Error:', err)
    sendError(err.message || 'Internal server error', 500)
  }
})

router.get('/:id', async (req, res, next) => {
  try {
    const { data, error } = await supabase
      .from('sessions')
      .select('*')
      .eq('id', req.params.id)
      .single()

    if (error || !data) {
      return res.status(404).json({ error: 'Session not found' })
    }

    res.json(data)
  } catch (err) {
    next(err)
  }
})

module.exports = router