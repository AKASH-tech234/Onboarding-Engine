const express = require('express');
const { upload } = require('../index.js');
const { extractText } = require('../parsers/extractText.js');
const { extractResumeSkills } = require('../ai/extractResumeSkills.js');
const { extractJDRequirements } = require('../ai/extractJDRequirements.js');
const { normalizeSkills } = require('../ai/normalizeSkills.js');
const { computeSkillGap } = require('../ai/computeSkillGap.js');
const { adaptivePathway } = require('../ai/adaptivePathway.js');
const { generateReasoningTrace } = require('../ai/generateReasoningTrace.js');
const supabase = require('../db/supabaseClient.js');

const router = express.Router();

router.post('/analyze', upload.fields([{ name: 'resume', maxCount: 1 }, { name: 'jd', maxCount: 1 }]), async (req, res, next) => {
  try {
    if (!req.files?.resume) return res.status(400).json({ error: 'Resume file is required' });
    if (!req.files?.jd && !req.body.jd_text) return res.status(400).json({ error: 'Job description is required' });

    let resumeText;
    try {
      const result = await extractText({ buffer: req.files.resume[0].buffer, mimetype: req.files.resume[0].mimetype });
      resumeText = result.text;
    } catch (e) {
      if (e.message === 'SCANNED_PDF') return res.status(400).json({ error: 'Resume appears to be a scanned image. Please upload a text-based PDF.' });
      if (e.message === 'UNSUPPORTED_FORMAT') return res.status(400).json({ error: 'Resume format not supported. Please use PDF or DOCX.' });
      throw e;
    }

    let jdText;
    if (req.body.jd_text) {
      jdText = req.body.jd_text;
    } else {
      try {
        const result = await extractText({ buffer: req.files.jd[0].buffer, mimetype: req.files.jd[0].mimetype });
        jdText = result.text;
      } catch (e) {
        if (e.message === 'SCANNED_PDF') return res.status(400).json({ error: 'Job description appears to be a scanned image. Please upload a text-based PDF.' });
        throw e;
      }
    }

    let resumeResult, jdResult;
    try { resumeResult = await extractResumeSkills(resumeText); }
    catch (e) {
      if (e.message === 'LLM_JSON_INVALID') return res.status(422).json({ error: 'Could not parse resume skills. Please try again.' });
      throw e;
    }
    
    try { jdResult = await extractJDRequirements(jdText); }
    catch (e) {
      if (e.message === 'LLM_JSON_INVALID') return res.status(422).json({ error: 'Could not parse job description. Please try again.' });
      throw e;
    }

    const allSkillNames = [
      ...resumeResult.skills.map(s => s.name),
      ...jdResult.skills.map(s => s.name)
    ];
    const normResults = await normalizeSkills(allSkillNames);
    const normMap = Object.fromEntries(normResults.map(r => [r.original, r]));

    resumeResult.skills = resumeResult.skills.map(s => ({ ...s, normalized_id: normMap[s.name]?.normalized_id }));
    jdResult.skills = jdResult.skills.map(s => ({ ...s, normalized_id: normMap[s.name]?.normalized_id }));

    const skillGap = computeSkillGap(resumeResult.skills, jdResult.skills);
    const pathwayResult = await adaptivePathway(skillGap, supabase);
    
    const reasoningTrace = await generateReasoningTrace({
      extractedSkills: resumeResult.skills,
      requiredSkills: jdResult.skills,
      skillGap,
      pathway: pathwayResult
    });

    const response = {
      session_id: null,
      candidate: {
        name: resumeResult.candidate_name,
        current_role: resumeResult.current_role,
        total_experience_years: resumeResult.total_experience_years
      },
      job_title: jdResult.job_title,
      skill_gap_summary: {
        total_gaps: skillGap.total_gaps,
        critical_gaps: skillGap.critical_gaps,
        already_met: skillGap.alreadyMet.length
      },
      pathway: pathwayResult,
      reasoning_trace: reasoningTrace,
      total_training_hrs: pathwayResult.total_training_hrs
    };

    const { data: sessionRow, error: dbError } = await supabase
      .from('sessions')
      .insert({
        resume_text: resumeText,
        jd_text: jdText,
        extracted_skills: resumeResult,
        required_skills: jdResult,
        skill_gap: skillGap,
        pathway: pathwayResult,
        reasoning_trace: reasoningTrace
      })
      .select('id')
      .single();
      
    if (dbError) throw dbError;

    response.session_id = sessionRow.id;
    res.status(201).json(response);

  } catch (err) {
    next(err);
  }
});

router.get('/:id', async (req, res, next) => {
  try {
    const { id } = req.params;
    const { data, error } = await supabase.from('sessions').select('*').eq('id', id).maybeSingle();

    if (error) throw error;
    if (!data) return res.status(404).json({ error: 'Session not found' });

    return res.json(data);
  } catch (error) {
    return next(error);
  }
});

module.exports = router;
