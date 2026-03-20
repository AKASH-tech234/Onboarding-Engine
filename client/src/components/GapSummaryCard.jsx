import SkillChips from './SkillChips';

export default function GapSummaryCard({ candidate, skillGapSummary, pathway }) {
  const allGaps = pathway.phases.flatMap(p => p.courses.map(c => ({
    skill: c.addresses_skill,
    current: c.gap_type === 'missing' ? 'none' : 'lower level',
    target: c.level,
    required: c.score_breakdown.gap_criticality === 1.0
  })));

  // Simple deduplication for UI display
  const uniqueGaps = Array.from(new Set(allGaps.map(g => g.skill)))
    .map(skill => allGaps.find(g => g.skill === skill));

  const requiredGaps = uniqueGaps.filter(g => g.required);
  const preferredGaps = uniqueGaps.filter(g => !g.required);
  
  // Dummy alreadyMet for mock setup, in real data it comes from skill_gap
  const alreadyMet = Array(skillGapSummary.already_met).fill({ skill: 'Assumed Skill', current: 'various', target: 'various' });

  const totalHrs = pathway.phases.reduce((sum, p) => sum + p.phase_duration_hrs, 0);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-800">{candidate.name || 'Candidate Profile'}</h2>
        <p className="text-slate-500 text-sm">{candidate.current_role} • {candidate.total_experience_years} yrs exp</p>
      </div>

      <div className="flex gap-2">
        <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-semibold">{skillGapSummary.total_gaps} gaps</span>
        <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs font-semibold">{skillGapSummary.critical_gaps} required</span>
        <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">{skillGapSummary.already_met} met</span>
      </div>

      <div>
        <h3 className="text-sm font-medium text-slate-700 mb-2">Already have</h3>
        <SkillChips items={alreadyMet} color="green" />
      </div>

      {requiredGaps.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-slate-700 mb-2">Missing (required)</h3>
          <SkillChips items={requiredGaps} color="red" />
        </div>
      )}

      {preferredGaps.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-slate-700 mb-2">Missing (preferred)</h3>
          <SkillChips items={preferredGaps} color="amber" />
        </div>
      )}

      <div className="mt-auto pt-4 border-t border-slate-200">
        <span className="text-sm font-medium text-slate-500">
          Est. training: <strong>{totalHrs.toFixed(1)}h</strong>
        </span>
      </div>
    </div>
  );
}
