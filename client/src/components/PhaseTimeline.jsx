import React from 'react';

export default function PhaseTimeline({ pathway, total_training_hrs }) {
  if (!pathway?.phases) return null;

  const validPhases = pathway.phases.filter(p => p.courses?.length > 0);
  if (validPhases.length === 0) return null;

  const phaseColors = {
    1: 'bg-blue-500',
    2: 'bg-purple-500',
    3: 'bg-orange-500',
    4: 'bg-slate-400'
  };

  return (
    <div className="flex items-center w-full px-6 py-4 border-t border-slate-200 bg-white relative z-10 shadow-sm mt-auto">
      {validPhases.map((phase, index) => (
        <React.Fragment key={phase.phase}>
          <div className="flex flex-col items-center">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-sm ${phaseColors[phase.phase] || 'bg-slate-400'}`}>
              {phase.phase}
            </div>
            <span className="text-[10px] font-semibold text-slate-700 mt-1 uppercase tracking-wider">{phase.phase_label}</span>
            <span className="text-[10px] text-slate-400 font-medium">{phase.phase_duration_hrs}h</span>
          </div>
          
          {index < validPhases.length - 1 && (
            <div className="flex-1 h-px bg-slate-200 mx-4 mt-[-16px]"></div>
          )}
        </React.Fragment>
      ))}

      <div className="ml-auto pl-6 border-l border-slate-200 mt-[-16px]">
        <div className="flex flex-col items-end">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Est.</span>
          <span className="text-sm font-bold text-slate-800">{total_training_hrs}h</span>
        </div>
      </div>
    </div>
  );
}
