import { formatDuration } from '../utils/formatDuration';

export default function CourseDrawer({ courseId, pathway, onClose }) {
  if (!courseId || !pathway?.phases) return null;

  const course = pathway.phases.flatMap((phase) => phase.courses).find((item) => item.id === courseId);
  if (!course) return null;

  const ScoreBar = ({ label, value }) => (
    <div className="mb-3 flex items-center gap-3 text-xs">
      <span className="w-28 text-slate-400">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/8">
        <div className="h-full rounded-full bg-gradient-to-r from-indigo-400 to-cyan-300" style={{ width: `${Math.max(0, Math.min(100, value * 100))}%` }} />
      </div>
      <span className="w-10 text-right font-mono font-medium text-slate-300">{(value * 100).toFixed(0)}%</span>
    </div>
  );

  return (
    <>
      <div className="fixed inset-0 z-30 bg-slate-950/60 backdrop-blur-sm transition-opacity" onClick={onClose} />
      <div className={`fixed right-0 top-0 z-40 h-full w-full max-w-md overflow-y-auto border-l border-white/10 bg-[linear-gradient(180deg,rgba(8,18,33,0.95),rgba(3,8,18,0.98))] shadow-[0_30px_80px_rgba(2,6,23,0.5)] backdrop-blur-2xl transition-transform duration-300 ${courseId ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="sticky top-0 z-10 border-b border-white/10 bg-slate-950/55 p-6 backdrop-blur-xl">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[11px] uppercase tracking-[0.24em] text-slate-400">Course detail</p>
              <h2 className="mt-2 pr-4 text-xl font-bold leading-tight text-slate-50">{course.title}</h2>
            </div>
            <button onClick={onClose} className="rounded-full border border-white/10 bg-white/6 px-3 py-1.5 text-sm font-semibold text-slate-300 transition-colors hover:bg-white/10 hover:text-white">
              Close
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-6 p-6">
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full border border-white/10 bg-indigo-400/12 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-indigo-100">
              {course.level}
            </span>
            <span className="rounded-full border border-white/10 bg-white/6 px-3 py-1 text-sm font-medium text-slate-300">
              {formatDuration(course.duration_hrs)}
            </span>
            <span className="rounded-full border border-white/10 bg-white/6 px-3 py-1 text-sm font-medium text-slate-300">
              {course.domain}
            </span>
          </div>

          <div className="rounded-[24px] border border-white/10 bg-white/5 p-5">
            <h3 className="mb-2 text-[11px] font-bold uppercase tracking-[0.24em] text-slate-400">Provider</h3>
            {course.url ? (
              <a href={course.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 text-sm font-semibold text-cyan-200 transition-colors hover:text-cyan-100">
                {course.provider} <span className="text-xs">↗</span>
              </a>
            ) : (
              <span className="text-sm font-medium text-slate-100">{course.provider || 'Internal'}</span>
            )}
          </div>

          <div className="rounded-[24px] border border-white/10 bg-white/5 p-5">
            <h3 className="mb-2 text-[11px] font-bold uppercase tracking-[0.24em] text-slate-400">Description</h3>
            <p className="text-sm leading-7 text-slate-300">{course.description}</p>
          </div>

          <div className="rounded-[24px] border border-amber-300/12 bg-amber-400/8 p-5">
            <h3 className="mb-2 text-[11px] font-bold uppercase tracking-[0.24em] text-amber-200">Addresses gap</h3>
            <p className="text-sm leading-6 text-amber-50">
              <strong>{course.addresses_skill}</strong> — {course.gap_type === 'missing' ? 'not found on resume' : 'level upgrade needed'}
            </p>
          </div>

          {course.score_breakdown && (
            <div className="rounded-[24px] border border-white/10 bg-white/5 p-5">
              <h3 className="mb-4 text-[11px] font-bold uppercase tracking-[0.24em] text-slate-400">Recommendation score</h3>
              <div className="rounded-2xl border border-white/8 bg-slate-950/30 p-4">
                <ScoreBar label="Gap Criticality" value={course.score_breakdown.gap_criticality} />
                <ScoreBar label="Impact Coverage" value={course.score_breakdown.impact_coverage} />
                <ScoreBar label="Level Fit" value={course.score_breakdown.level_fit} />
                <ScoreBar label="Efficiency" value={course.score_breakdown.efficiency} />
              </div>
            </div>
          )}

          {course.prerequisites?.length > 0 && (
            <div className="rounded-[24px] border border-white/10 bg-white/5 p-5">
              <h3 className="mb-3 text-[11px] font-bold uppercase tracking-[0.24em] text-slate-400">Prerequisites</h3>
              <ul className="space-y-2">
                {course.prerequisites.map((prereqId) => {
                  const prereqCourse = pathway.phases.flatMap((phase) => phase.courses).find((item) => item.id === prereqId);
                  return (
                    <li key={prereqId} className="rounded-2xl border border-white/8 bg-slate-950/25 px-4 py-3 text-sm text-slate-300">
                      {prereqCourse?.title || 'Unknown course'}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
