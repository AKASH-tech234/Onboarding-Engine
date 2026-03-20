export const mockData = {
  session_id: '123e4567-e89b-12d3-a456-426614174000',
  candidate: { 
    name: 'Alex Chen', 
    current_role: 'Junior Dev', 
    total_experience_years: 3 
  },
  skill_gap_summary: { 
    total_gaps: 4, 
    critical_gaps: 3, 
    already_met: 5 
  },
  pathway: {
    phases: [
      {
        phase: 1,
        phase_label: "Foundation",
        courses: [
          {
            id: "c1",
            title: "Docker Fundamentals",
            description: "Learn basic containerization.",
            level: "intermediate",
            level_num: 2,
            duration_hrs: 4.0,
            provider: "Docker Docs",
            url: "https://docs.docker.com",
            addresses_skill: "Docker",
            gap_type: "missing",
            score: 0.85,
            score_breakdown: {
              gap_criticality: 1.0,
              impact_coverage: 1.0,
              level_fit: 1.0,
              efficiency: 0.1
            },
            prerequisites: []
          }
        ],
        phase_duration_hrs: 4.0
      }
    ]
  },
  reasoning_trace: { 
    candidate_assessment: 'Alex is a junior developer with strong JavaScript skills.', 
    gap_identification: 'Needs Docker for the required deployment tasks.', 
    course_selection_rationale: 'Docker Fundamentals selected as it matches the missing skill perfectly.', 
    pathway_ordering_logic: 'Docker must be learned before Kubernetes.', 
    estimated_time_to_competency: '4 hours total.', 
    raw: 'Raw reasoning text here...' 
  },
  total_training_hrs: 24.5
};
