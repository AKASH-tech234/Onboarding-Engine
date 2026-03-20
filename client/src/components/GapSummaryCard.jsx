import SkillChips from './SkillChips';

export default function GapSummaryCard({ candidate, skillGapSummary, pathway }) {
  const phases = pathway?.phases || [];
  const allGaps = phases.flatMap((phase) =>
    phase.courses.map((course) => ({
      skill: course.addresses_skill,
      current: course.gap_type === 'missing' ? 'none' : 'lower level',
      target: course.level,
      required: course.score_breakdown?.gap_criticality === 1.0,
    }))
  );

  const uniqueGaps = Array.from(new Set(allGaps.map((item) => item.skill))).map((skill) =>
    allGaps.find((item) => item.skill === skill)
  );

  const requiredGaps = uniqueGaps.filter((item) => item.required);
  const preferredGaps = uniqueGaps.filter((item) => !item.required);
  const alreadyMet = Array(skillGapSummary.already_met).fill({
    skill: 'Assumed skill',
    current: 'various',
    target: 'various',
  });

  const totalHours = phases.reduce((sum, phase) => sum + phase.phase_duration_hrs, 0);
  const profileItems = [
    {
      label: 'Role',
      value: candidate.current_role || 'Profile under review',
    },
    {
      label: 'Experience',
      value: candidate.total_experience_years ? `${candidate.total_experience_years} years` : 'Not specified',
    },
    {
      label: 'Phases',
      value: `${phases.length} roadmap stages`,
    },
  ];

  return (
    <div className="flex h-full flex-col gap-6">
      <div className="rounded-[28px] border border-white/12 bg-white/6 p-5 shadow-[0_18px_40px_rgba(2,6,23,0.25)]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.26em] text-slate-400">Candidate</p>
        <h2 className="mt-3 text-2xl font-extrabold tracking-tight text-slate-50">
          {candidate.name || 'Candidate Profile'}
        </h2>
        <div className="mt-5 grid gap-3">
          {profileItems.map((item) => (
            <div key={item.label} className="rounded-2xl border border-white/8 bg-slate-950/25 px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">{item.label}</p>
              <p className="mt-1 text-sm font-semibold text-slate-100">{item.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <StatBadge label="Gaps" value={skillGapSummary.total_gaps} tone="rose" />
        <StatBadge label="Required" value={skillGapSummary.critical_gaps} tone="amber" />
        <StatBadge label="Met" value={skillGapSummary.already_met} tone="emerald" />
      </div>

      <div className="rounded-[26px] border border-white/10 bg-white/5 p-5">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-slate-300">Already covered</h3>
        <SkillChips items={alreadyMet} color="green" />
      </div>

      {requiredGaps.length > 0 && (
        <div className="rounded-[26px] border border-white/10 bg-white/5 p-5">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-slate-300">Required gaps</h3>
          <SkillChips items={requiredGaps} color="red" />
        </div>
      )}

      {preferredGaps.length > 0 && (
        <div className="rounded-[26px] border border-white/10 bg-white/5 p-5">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-slate-300">Stretch skills</h3>
          <SkillChips items={preferredGaps} color="amber" />
        </div>
      )}

      <div className="mt-auto rounded-[26px] border border-indigo-300/15 bg-gradient-to-br from-indigo-400/10 to-cyan-400/10 p-5 shadow-[0_18px_40px_rgba(15,23,42,0.25)]">
        <p className="text-[11px] uppercase tracking-[0.24em] text-slate-400">Estimated training</p>
        <div className="mt-2 flex items-end justify-between">
          <span className="text-3xl font-extrabold text-white">{totalHours.toFixed(1)}h</span>
          <span className="text-sm text-slate-300">guided learning path</span>
        </div>
      </div>
    </div>
  );
}

function StatBadge({ label, value, tone }) {
  const toneClasses = {
    rose: 'border-rose-400/20 bg-rose-400/10 text-rose-100',
    amber: 'border-amber-400/20 bg-amber-400/10 text-amber-100',
    emerald: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-100',
  };

  return (
    <div className={`rounded-2xl border p-4 text-center shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] ${toneClasses[tone]}`}>
      <p className="text-[10px] uppercase tracking-[0.24em] opacity-80">{label}</p>
      <p className="mt-2 text-2xl font-extrabold">{value}</p>
    </div>
  );
}
