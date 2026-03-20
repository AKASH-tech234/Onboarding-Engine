const assert = require("node:assert/strict");

const { computeSkillGap } = require("../ai/computeSkillGap");

function runComputeSkillGapTests() {
  {
    const extractedSkills = [
      { normalized_id: "react-id", name: "React", level: "advanced" },
      { normalized_id: "sql-id", name: "SQL", level: "intermediate" },
    ];

    const requiredSkills = [
      { normalized_id: "react-id", name: "React", level: "intermediate", required: true },
      { normalized_id: "sql-id", name: "SQL", level: "intermediate", required: true },
    ];

    const result = computeSkillGap(extractedSkills, requiredSkills);

    assert.equal(result.total_gaps, 0);
    assert.equal(result.critical_gaps, 0);
    assert.equal(result.gaps.length, 0);
    assert.equal(result.missing.length, 0);
    assert.equal(result.alreadyMet.length, requiredSkills.length);
  }

  {
    const extractedSkills = [];
    const requiredSkills = [
      { normalized_id: "docker-id", name: "Docker", level: "beginner", required: true },
      { normalized_id: "aws-id", name: "AWS", level: "intermediate", required: true },
    ];

    const result = computeSkillGap(extractedSkills, requiredSkills);

    assert.equal(result.gaps.length, 0);
    assert.equal(result.missing.length, 2);
    assert.equal(result.total_gaps, 2);
    assert.equal(result.critical_gaps, 2);
    assert.deepEqual(result.missing[1], {
      skill: "AWS",
      skill_id: "aws-id",
      current: null,
      current_num: 0,
      target: "intermediate",
      target_num: 2,
      gap_size: 2,
      required: true,
    });
  }

  {
    const extractedSkills = [
      { normalized_id: "k8s-id", name: "Kubernetes", level: "beginner" },
    ];

    const requiredSkills = [
      { normalized_id: "k8s-id", name: "Kubernetes", level: "advanced", required: true },
    ];

    const result = computeSkillGap(extractedSkills, requiredSkills);

    assert.equal(result.gaps.length, 1);
    assert.deepEqual(result.gaps[0], {
      skill: "Kubernetes",
      skill_id: "k8s-id",
      current: "beginner",
      current_num: 1,
      target: "advanced",
      target_num: 3,
      gap_size: 2,
      required: true,
    });
  }

  {
    const extractedSkills = [
      { normalized_id: "python-id", name: "Python", level: "beginner" },
    ];

    const requiredSkills = [
      { normalized_id: "python-id", name: "Python", level: "advanced", required: true },
      { normalized_id: "docker-id", name: "Docker", level: "beginner", required: false },
    ];

    const result = computeSkillGap(extractedSkills, requiredSkills);

    assert.equal(result.total_gaps, 2);
    assert.equal(result.critical_gaps, 1);
    assert.equal(result.gaps.length, 1);
    assert.equal(result.missing.length, 1);
    assert.equal(result.missing[0].required, false);
  }

  {
    const extractedSkills = [
      { normalized_id: "node-id", name: "Node.js", level: "advanced" },
    ];

    const requiredSkills = [
      { normalized_id: "node-id", name: "Node.js", level: "beginner", required: true },
    ];

    const result = computeSkillGap(extractedSkills, requiredSkills);

    assert.equal(result.total_gaps, 0);
    assert.deepEqual(result.alreadyMet, [
      {
        skill: "Node.js",
        current: "advanced",
        target: "beginner",
      },
    ]);
  }
}

module.exports = {
  runComputeSkillGapTests,
};
