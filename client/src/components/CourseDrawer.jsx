import { formatDuration } from '../utils/formatDuration';

export default function CourseDrawer({ courseId, pathway, onClose }) {
  if (!courseId || !pathway?.phases) return null;

  const course = pathway.phases.flatMap(p => p.courses).find(c => c.id === courseId);
  if (!course) return null;

  const ScoreBar = ({ label, value }) => (
    <div className="flex items-center gap-2 text-xs mb-1.5">
      <span className="w-32 text-slate-500">{label}</span>
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${value * 100}%` }} />
      </div>
      <span className="w-8 text-right text-slate-600 font-medium font-mono">{(value * 100).toFixed(0)}%</span>
    </div>
  );

  return (
    <>
      <div 
        className="fixed inset-0 bg-slate-900/20 z-10 transition-opacity"
        onClick={onClose}
      />
      <div className={`fixed top-0 right-0 h-full w-80 bg-white shadow-2xl z-20 overflow-y-auto transform transition-transform duration-300 ${courseId ? 'translate-x-0' : 'translate-x-full'}`}>
        <div className="p-5 border-b border-slate-100 flex justify-between items-start sticky top-0 bg-white z-10">
          <h2 className="font-semibold text-lg text-slate-800 leading-tight pr-4">{course.title}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-2xl leading-none">&times;</button>
        </div>
        
        <div className="p-5 flex flex-col gap-6">
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-1 bg-slate-100 text-slate-700 text-xs font-semibold rounded-md uppercase tracking-wide">
              {course.level}
            </span>
            <span className="text-sm font-medium text-slate-500">
              ⏱ {formatDuration(course.duration_hrs)}
            </span>
          </div>

          <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Provider</h3>
            {course.url ? (
              <a href={course.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-800 hover:underline font-medium text-sm flex items-center gap-1">
                {course.provider} <span className="text-[10px]">↗</span>
              </a>
            ) : (
              <span className="text-sm font-medium text-slate-700">{course.provider || 'Internal'}</span>
            )}
          </div>

          <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Description</h3>
            <p className="text-sm text-slate-600 leading-relaxed">{course.description}</p>
          </div>

          <div className="bg-amber-50 rounded-lg p-3 border border-amber-100">
            <h3 className="text-xs font-bold text-amber-800 uppercase tracking-wider mb-1">Addresses Gap</h3>
            <p className="text-sm text-amber-900">
              <strong>{course.addresses_skill}</strong> — {course.gap_type === 'missing' ? 'not found on resume' : 'level upgrade needed'}
            </p>
          </div>

          {course.score_breakdown && (
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Why this course?</h3>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                <ScoreBar label="Gap Criticality" value={course.score_breakdown.gap_criticality} />
                <ScoreBar label="Impact Coverage" value={course.score_breakdown.impact_coverage} />
                <ScoreBar label="Level Fit" value={course.score_breakdown.level_fit} />
                <ScoreBar label="Efficiency" value={course.score_breakdown.efficiency} />
              </div>
            </div>
          )}
          
          {course.prerequisites?.length > 0 && (
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Prerequisites</h3>
              <ul className="list-disc pl-4 space-y-1">
                {course.prerequisites.map(prereqId => {
                  const prereqCourse = pathway.phases.flatMap(p => p.courses).find(c => c.id === prereqId);
                  return (
                    <li key={prereqId} className="text-sm text-slate-600">
                      {prereqCourse?.title || 'Unknown Course'}
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
