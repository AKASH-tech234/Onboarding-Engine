import { useState, useRef, useEffect } from 'react';

const sectionLabels = {
  candidate_assessment: 'Candidate Assessment',
  gap_identification: 'Gap Identification',
  course_selection_rationale: 'Course Selection',
  pathway_ordering_logic: 'Ordering Logic',
  estimated_time_to_competency: 'Time to Competency',
};

export default function ReasoningTrace({ trace, activeSection }) {
  if (!trace) return null;

  if (!trace.candidate_assessment && trace.raw) {
    return (
      <div className="space-y-4">
        <h2 className="border-b border-white/10 pb-3 text-lg font-bold text-slate-50">Why this pathway?</h2>
        <div className="rounded-[28px] border border-white/10 bg-white/5 p-5 text-sm leading-7 text-slate-300">
          {trace.raw.split('\n\n').map((paragraph, index) => (
            <p key={index}>{paragraph}</p>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="border-b border-white/10 pb-3 text-lg font-bold text-slate-50">
        Why this pathway?
      </h2>
      <div className="space-y-3">
        {Object.entries(sectionLabels).map(([key, label], index) => {
          if (!trace[key]) return null;
          return (
            <TraceSection
              key={key}
              id={key}
              label={`Step ${index + 1}: ${label}`}
              content={trace[key]}
              isActive={activeSection === key}
              defaultOpen={key === 'candidate_assessment'}
            />
          );
        })}
      </div>
    </div>
  );
}

function TraceSection({ label, content, isActive, defaultOpen }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const ref = useRef(null);

  useEffect(() => {
    if (isActive) {
      setIsOpen(true);
      ref.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [isActive]);

  return (
    <div ref={ref} className={`overflow-hidden rounded-[24px] border transition-all duration-300 ${isActive ? 'border-indigo-300/40 bg-indigo-400/10 shadow-[0_18px_35px_rgba(99,102,241,0.14)]' : 'border-white/10 bg-white/5 hover:bg-white/[0.07]'}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between px-5 py-4 text-left transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-300/50"
      >
        <span className="text-sm font-semibold tracking-wide text-slate-100">{label}</span>
        <svg className={`h-4 w-4 text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="border-t border-white/8 px-5 pb-5 pt-3">
          <div className="space-y-3 text-sm leading-7 text-slate-300">
            {content.split('\n\n').map((paragraph, i) => {
              if (paragraph.trim().startsWith('-')) {
                const items = paragraph.split('\n').filter((line) => line.trim().startsWith('-'));
                return (
                  <ul key={i} className="my-2 list-disc space-y-1 pl-5">
                    {items.map((item, j) => (
                      <li key={j}>{item.replace(/^-/, '').trim()}</li>
                    ))}
                  </ul>
                );
              }

              return <p key={i}>{paragraph}</p>;
            })}
          </div>
        </div>
      )}
    </div>
  );
}
