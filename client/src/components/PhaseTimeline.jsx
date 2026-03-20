import React from 'react';

export default function PhaseTimeline({ pathway, total_training_hrs }) {
  if (!pathway?.phases) return null;

  const validPhases = pathway.phases.filter((phase) => phase.courses?.length > 0);
  if (validPhases.length === 0) return null;

  const phaseColors = {
    1: 'from-cyan-400 to-sky-500',
    2: 'from-indigo-400 to-violet-500',
    3: 'from-amber-400 to-orange-500',
    4: 'from-slate-400 to-slate-500',
  };

  return (
    <div className="relative z-10 border-t border-white/10 bg-slate-950/65 px-5 py-4">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center">
        <div className="flex min-w-0 flex-1 items-center gap-4 overflow-x-auto pb-1">
          {validPhases.map((phase, index) => (
            <React.Fragment key={phase.phase}>
              <div className="flex min-w-fit flex-col items-center">
                <div className={`flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br text-sm font-bold text-white shadow-[0_12px_25px_rgba(15,23,42,0.25)] ${phaseColors[phase.phase] || 'from-slate-400 to-slate-500'}`}>
                  {phase.phase}
                </div>
                <span className="mt-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-200">{phase.phase_label}</span>
                <span className="text-xs text-slate-400">{phase.phase_duration_hrs}h</span>
              </div>

              {index < validPhases.length - 1 && (
                <div className="h-px min-w-[56px] flex-1 bg-gradient-to-r from-white/10 to-white/0" />
              )}
            </React.Fragment>
          ))}
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/6 px-4 py-3">
          <div className="flex flex-col items-end">
            <span className="text-[10px] font-bold uppercase tracking-[0.24em] text-slate-400">Total estimate</span>
            <span className="text-lg font-bold text-slate-50">{total_training_hrs}h</span>
          </div>
        </div>
      </div>
    </div>
  );
}
