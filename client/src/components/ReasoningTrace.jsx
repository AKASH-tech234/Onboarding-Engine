import { useState, useRef, useEffect } from 'react';

const sectionLabels = {
  candidate_assessment: 'Candidate Assessment',
  gap_identification: 'Gap Identification',
  course_selection_rationale: 'Course Selection',
  pathway_ordering_logic: 'Ordering Logic',
  estimated_time_to_competency: 'Time to Competency'
};

export default function ReasoningTrace({ trace, activeSection }) {
  if (!trace) return null;

  // If only raw exists, render a simple fallback
  if (!trace.candidate_assessment && trace.raw) {
    return (
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-800 border-b border-slate-200 pb-2">Reasoning</h2>
        <div className="text-sm text-slate-600 space-y-2">
          {trace.raw.split('\n\n').map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-bold text-slate-800 pb-2 border-b border-slate-200">
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

function TraceSection({ id, label, content, isActive, defaultOpen }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const ref = useRef(null);

  useEffect(() => {
    if (isActive) {
      setIsOpen(true);
      ref.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [isActive]);

  return (
    <div ref={ref} className={`border rounded-lg ${isActive ? 'border-blue-300 ring-1 ring-blue-100' : 'border-slate-200'} bg-white overflow-hidden transition-all duration-200`}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex justify-between items-center py-3 px-4 bg-slate-50/50 hover:bg-slate-50 transition-colors focus:outline-none"
      >
        <span className="font-semibold text-slate-700 text-sm tracking-wide">{label}</span>
        <svg 
          className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} 
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {isOpen && (
        <div className="px-4 pb-4 pt-1 border-t border-slate-100">
          <div className="text-sm text-slate-600 space-y-2 leading-relaxed">
            {content.split('\n\n').map((paragraph, i) => {
              if (paragraph.trim().startsWith('-')) {
                const items = paragraph.split('\n').filter(l => l.trim().startsWith('-'));
                return (
                  <ul key={i} className="list-disc pl-5 space-y-1 my-2">
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
