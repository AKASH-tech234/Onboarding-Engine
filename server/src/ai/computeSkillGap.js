const { levelToNum } = require("../utils/levelToNum");

function computeSkillGap(extractedSkills, requiredSkills) {
  const safeExtractedSkills = Array.isArray(extractedSkills) ? extractedSkills : [];
  const safeRequiredSkills = Array.isArray(requiredSkills) ? requiredSkills : [];

  const gaps = [];
  const missing = [];
  const alreadyMet = [];

  for (const requirement of safeRequiredSkills) {
    const targetNum = levelToNum(requirement.level);
    const currentSkill = safeExtractedSkills.find(
      (skill) => skill.normalized_id === requirement.normalized_id
    );

    if (!currentSkill) {
      missing.push({
        skill: requirement.name,
        skill_id: requirement.normalized_id,
        current: null,
        current_num: 0,
        target: requirement.level,
        target_num: targetNum,
        gap_size: targetNum,
        required: Boolean(requirement.required),
      });

      continue;
    }

    const currentNum = levelToNum(currentSkill.level);

    if (currentNum < targetNum) {
      gaps.push({
        skill: requirement.name,
        skill_id: requirement.normalized_id,
        current: currentSkill.level,
        current_num: currentNum,
        target: requirement.level,
        target_num: targetNum,
        gap_size: targetNum - currentNum,
        required: Boolean(requirement.required),
      });

      continue;
    }

    alreadyMet.push({
      skill: requirement.name,
      current: currentSkill.level,
      target: requirement.level,
    });
  }

  const criticalGaps = [...gaps, ...missing].filter((gap) => gap.required).length;

  return {
    gaps,
    missing,
    alreadyMet,
    total_gaps: gaps.length + missing.length,
    critical_gaps: criticalGaps,
  };
}

module.exports = {
  computeSkillGap,
};
