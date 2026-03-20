const assert = require("node:assert/strict");

const {
  adaptivePathway,
  assignPhase,
  scoreCandidate,
  topologicalSort,
} = require("../ai/adaptivePathway");

async function runAdaptivePathwayTests() {
  assert.deepEqual(
    assignPhase({ level_num: 1, gap: { required: true } }),
    { phase: 1, phase_label: "Foundation" }
  );

  assert.deepEqual(
    assignPhase({ level_num: 2, gap: { required: true } }),
    { phase: 2, phase_label: "Core Competency" }
  );

  {
    const courses = [
      { id: "kubernetes", score: 0.9, prerequisites: ["docker"] },
      { id: "docker", score: 0.7, prerequisites: [] },
      { id: "aws", score: 0.8, prerequisites: [] },
    ];

    const result = topologicalSort(courses);
    const dockerIndex = result.findIndex((course) => course.id === "docker");
    const kubernetesIndex = result.findIndex((course) => course.id === "kubernetes");

    assert.notEqual(dockerIndex, -1);
    assert.notEqual(kubernetesIndex, -1);
    assert.ok(dockerIndex < kubernetesIndex);
  }

  {
    const result = scoreCandidate(
      {
        impact: 0.9,
        level_num: 2,
        duration_hrs: 4,
      },
      {
        required: true,
        target_num: 2,
      }
    );

    assert.ok(result.total > 0);
    assert.ok(result.total <= 1.1);
    assert.ok(result.gap_criticality >= 0 && result.gap_criticality <= 1);
    assert.ok(result.impact_coverage >= 0 && result.impact_coverage <= 1);
    assert.ok(result.level_fit >= 0 && result.level_fit <= 1);
    assert.ok(result.efficiency >= 0 && result.efficiency <= 1);
  }

  {
    const result = await adaptivePathway(
      {
        gaps: [],
        missing: [],
      },
      {}
    );

    assert.deepEqual(result, {
      phases: [],
      total_training_hrs: 0,
    });
  }

  {
    const fakeSupabase = {
      async rpc(name, params) {
        if (name === "match_courses_by_skill" && params.p_skill_id === "docker-id") {
          return {
            data: [
              {
                id: "docker",
                title: "Docker Foundations",
                level: "beginner",
                level_num: 1,
                duration_hrs: 4,
                impact: 0.9,
                prerequisites: [],
              },
              {
                id: "kubernetes",
                title: "Kubernetes Core",
                level: "intermediate",
                level_num: 2,
                duration_hrs: 6,
                impact: 0.8,
                prerequisites: ["docker"],
              },
            ],
            error: null,
          };
        }

        if (name === "match_courses_by_skill" && params.p_skill_id === "js-id") {
          return {
            data: [
              {
                id: "javascript",
                title: "JavaScript Essentials",
                level: "beginner",
                level_num: 1,
                duration_hrs: 5,
                impact: 0.85,
                prerequisites: [],
              },
              {
                id: "react",
                title: "React Basics",
                level: "intermediate",
                level_num: 2,
                duration_hrs: 7,
                impact: 0.88,
                prerequisites: ["javascript"],
              },
            ],
            error: null,
          };
        }

        if (name === "match_courses_by_vector") {
          return {
            data: [],
            error: null,
          };
        }

        return {
          data: [],
          error: null,
        };
      },
    };

    const result = await adaptivePathway(
      {
        gaps: [
          {
            skill: "JavaScript",
            skill_id: "js-id",
            current: "beginner",
            current_num: 1,
            target: "intermediate",
            target_num: 2,
            gap_size: 1,
            required: true,
          },
        ],
        missing: [
          {
            skill: "Docker",
            skill_id: "docker-id",
            current: null,
            current_num: 0,
            target: "beginner",
            target_num: 1,
            gap_size: 1,
            required: true,
          },
        ],
      },
      fakeSupabase
    );

    assert.equal(result.phases.length, 2);
    assert.equal(result.total_training_hrs, 22);

    const allCourses = result.phases.flatMap((phase) => phase.courses);
    const dockerIndex = allCourses.findIndex((course) => course.id === "docker");
    const kubernetesIndex = allCourses.findIndex((course) => course.id === "kubernetes");
    const javascriptIndex = allCourses.findIndex((course) => course.id === "javascript");
    const reactIndex = allCourses.findIndex((course) => course.id === "react");

    assert.ok(dockerIndex < kubernetesIndex);
    assert.ok(javascriptIndex < reactIndex);

    for (const course of allCourses) {
      assert.ok(typeof course.score === "number");
      assert.ok(course.score > 0);
      assert.ok(course.score_breakdown);
      assert.ok(typeof course.score_breakdown.gap_criticality === "number");
      assert.ok(typeof course.score_breakdown.impact_coverage === "number");
      assert.ok(typeof course.score_breakdown.level_fit === "number");
      assert.ok(typeof course.score_breakdown.efficiency === "number");
    }
  }

  {
    const result = topologicalSort([
      {
        id: "advanced-sql",
        score: 0.95,
        prerequisites: ["sql-basics"],
      },
    ]);

    assert.deepEqual(result.map((course) => course.id), ["advanced-sql"]);
  }
}

module.exports = {
  runAdaptivePathwayTests,
};
