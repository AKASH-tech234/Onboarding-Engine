const { levelToNum } = require('../utils/levelToNum')

function computeSkillGap(extractedSkills, requiredSkills) {
  const gaps = []
  const missing = []
  const alreadyMet = []

  for (const req of requiredSkills) {
    const current = extractedSkills.find(s => s.normalized_id === req.normalized_id)

    if (!current) {
      missing.push({
        skill: req.name,
        skill_id: req.normalized_id,
        current: null,
        current_num: 0,
        target: req.level,
        target_num: levelToNum(req.level),
        gap_size: levelToNum(req.level),
        required: req.required
      })
    } else if (levelToNum(current.level) < levelToNum(req.level)) {
      gaps.push({
        skill: req.name,
        skill_id: req.normalized_id,
        current: current.level,
        current_num: levelToNum(current.level),
        target: req.level,
        target_num: levelToNum(req.level),
        gap_size: levelToNum(req.level) - levelToNum(current.level),
        required: req.required
      })
    } else {
      alreadyMet.push({
        skill: req.name,
        current: current.level,
        target: req.level
      })
    }
  }

  return {
    gaps,
    missing,
    alreadyMet,
    total_gaps: gaps.length + missing.length,
    critical_gaps: [...gaps, ...missing].filter(g => g.required).length
  }
}

module.exports = { computeSkillGap }