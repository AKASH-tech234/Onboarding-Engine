import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useSession } from '../hooks/useSession';
import GapSummaryCard from '../components/GapSummaryCard';
import PathwayFlow from '../components/PathwayFlow';
import CourseDrawer from '../components/CourseDrawer';
import ReasoningTrace from '../components/ReasoningTrace';
import PhaseTimeline from '../components/PhaseTimeline';

export default function ResultsPage() {
  const { id } = useParams();
  const { data, isLoading, error } = useSession(id);
  const [selectedCourseId, setSelectedCourseId] = useState(null);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <svg className="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-screen items-center justify-center flex-col gap-4 bg-slate-50">
        <p className="text-red-600 font-medium">{error || 'Session failed to load'}</p>
        <Link to="/" className="text-blue-600 hover:underline">← Start Over</Link>
      </div>
    );
  }

  // Handle empty pathway scenario (Day 6 requirement handled here)
  if (data.skill_gap_summary.total_gaps === 0) {
    return (
      <div className="flex h-screen bg-slate-50">
        <div className="hidden lg:block w-[280px] border-r border-slate-200 bg-white p-5 overflow-y-auto">
          <GapSummaryCard candidate={data.candidate} skillGapSummary={data.skill_gap_summary} pathway={data.pathway} />
        </div>
        <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8">
          <div className="text-green-500 text-6xl">✓</div>
          <h2 className="text-2xl font-bold text-slate-800">No Skill Gaps Found</h2>
          <p className="text-slate-500 text-center max-w-md">
            This candidate already meets all requirements for the <strong>{data.job_title || 'target role'}</strong>.
          </p>
          <Link to="/" className="mt-4 px-6 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 font-medium rounded-lg transition-colors">
            Analyze another candidate
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-slate-50 flex flex-col md:flex-row overflow-hidden">
      {/* Left Panel: Gap Summary */}
      <div className="w-full md:w-[280px] border-b md:border-b-0 md:border-r border-slate-200 bg-white p-5 overflow-y-auto shrink-0 md:max-h-full max-h-52">
        <GapSummaryCard 
          candidate={data.candidate} 
          skillGapSummary={data.skill_gap_summary} 
          pathway={data.pathway} 
        />
      </div>

      {/* Center Panel: Pathway Flow */}
      <div className="flex-1 relative overflow-hidden flex flex-col bg-slate-50/50">
        <div className="absolute top-4 left-4 z-10">
          <Link to="/" className="px-3 py-1.5 bg-white border border-slate-200 rounded-md text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-50 shadow-sm transition-all focus:outline-none">
            ← Back
          </Link>
        </div>
        
        <PathwayFlow 
          pathway={data.pathway} 
          onNodeClick={setSelectedCourseId} 
        />
        
        <div className="mt-auto shrink-0 border-t border-slate-200">
          <PhaseTimeline pathway={data.pathway} total_training_hrs={data.total_training_hrs} />
        </div>
      </div>

      {/* Right Panel: Reasoning Trace */}
      <div className="hidden lg:block w-[340px] bg-slate-50 border-l border-slate-200 p-5 overflow-y-auto shrink-0 shadow-inner">
        <ReasoningTrace trace={data.reasoning_trace} activeSection={null} />
      </div>

      {/* Slide-in Drawer */}
      <CourseDrawer 
        courseId={selectedCourseId} 
        pathway={data.pathway} 
        onClose={() => setSelectedCourseId(null)} 
      />
    </div>
  );
}
