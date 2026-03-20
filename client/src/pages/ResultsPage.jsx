import { useState } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { useSession } from '../hooks/useSession';
import GapSummaryCard from '../components/GapSummaryCard';
import PathwayFlow from '../components/PathwayFlow';
import CourseDrawer from '../components/CourseDrawer';
import ReasoningTrace from '../components/ReasoningTrace';
import PhaseTimeline from '../components/PhaseTimeline';

export default function ResultsPage() {
  const { id } = useParams();
  const location = useLocation();
  const initialData = location.state?.sessionData || null;
  const { data, isLoading, error } = useSession(id, initialData);
  const [selectedCourseId, setSelectedCourseId] = useState(null);

  if (isLoading) {
    return (
      <div className="app-shell flex min-h-screen items-center justify-center px-6">
        <div className="glass-panel rounded-[32px] px-10 py-8 text-center">
          <svg className="mx-auto h-10 w-10 animate-spin text-indigo-200" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="mt-4 text-sm font-semibold uppercase tracking-[0.24em] text-slate-300">Loading analysis</p>
          <p className="mt-2 text-sm text-slate-400">Preparing the adaptive pathway and course graph.</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="app-shell flex min-h-screen items-center justify-center px-6">
        <div className="glass-panel max-w-lg rounded-[32px] p-10 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-rose-200">Unable to load session</p>
          <p className="mt-4 text-lg font-semibold text-white">{error || 'Session failed to load'}</p>
          <Link to="/" className="mt-6 inline-flex rounded-full border border-white/10 bg-white/6 px-5 py-2.5 text-sm font-semibold text-slate-100 transition-colors hover:bg-white/10">← Start over</Link>
        </div>
      </div>
    );
  }

  if (data.skill_gap_summary.total_gaps === 0) {
    return (
      <div className="app-shell min-h-screen px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid min-h-[calc(100vh-3rem)] gap-6 lg:grid-cols-[320px_1fr]">
          <div className="glass-panel overflow-y-auto rounded-[32px] p-5">
            <GapSummaryCard candidate={data.candidate} skillGapSummary={data.skill_gap_summary} pathway={data.pathway} />
          </div>
          <div className="glass-panel flex flex-col items-center justify-center rounded-[32px] p-8 text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-full border border-emerald-300/15 bg-emerald-400/12 text-4xl text-emerald-200">✓</div>
            <h2 className="mt-6 text-3xl font-bold text-white">No skill gaps found</h2>
            <p className="mt-3 max-w-md text-slate-300">
              This candidate already meets all requirements for the <strong>{data.job_title || 'target role'}</strong>.
            </p>
            <Link to="/" className="mt-6 rounded-full border border-white/10 bg-white/6 px-6 py-3 text-sm font-semibold text-slate-100 transition-colors hover:bg-white/10">
              Analyze another candidate
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell min-h-screen px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-2.5rem)] max-w-[1680px] flex-col gap-5">
        <header className="glass-panel rounded-[30px] px-5 py-4">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-[0.28em] text-slate-400">Adaptive result</p>
              <h1 className="mt-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">
                {data.candidate?.name || 'Candidate'} → {data.job_title || 'Target role'}
              </h1>
              <p className="mt-2 text-sm leading-7 text-slate-300">
                Review the skill gap summary, explore the dependency graph, and inspect the reasoning trace for each recommendation.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <MetricPill label="Total gaps" value={data.skill_gap_summary.total_gaps} />
              <MetricPill label="Critical gaps" value={data.skill_gap_summary.critical_gaps} />
              <MetricPill label="Training hours" value={data.total_training_hrs} />
              <Link to="/" className="inline-flex items-center rounded-full border border-white/10 bg-white/6 px-4 py-2 text-sm font-semibold text-slate-100 transition-colors hover:bg-white/10">
                ← Back
              </Link>
            </div>
          </div>
        </header>

        <div className="grid flex-1 gap-5 2xl:grid-cols-[320px_minmax(0,1fr)_360px]">
          <aside className="glass-panel order-2 rounded-[32px] p-5 md:order-1 2xl:overflow-y-auto">
            <GapSummaryCard candidate={data.candidate} skillGapSummary={data.skill_gap_summary} pathway={data.pathway} />
          </aside>

          <section className="order-1 flex min-h-[620px] flex-col rounded-[32px] 2xl:order-2">
            <div className="flex-1 overflow-hidden">
              <PathwayFlow pathway={data.pathway} onNodeClick={setSelectedCourseId} />
            </div>
            <div className="mt-4 overflow-hidden rounded-[28px] border border-white/10 bg-white/5">
              <PhaseTimeline pathway={data.pathway} total_training_hrs={data.total_training_hrs} />
            </div>
          </section>

          <aside className="glass-panel order-3 rounded-[32px] p-5 2xl:overflow-y-auto">
            <ReasoningTrace trace={data.reasoning_trace} activeSection={null} />
          </aside>
        </div>
      </div>

      <CourseDrawer courseId={selectedCourseId} pathway={data.pathway} onClose={() => setSelectedCourseId(null)} />
    </div>
  );
}

function MetricPill({ label, value }) {
  return (
    <div className="rounded-full border border-white/10 bg-white/6 px-4 py-2 text-sm font-semibold text-slate-100">
      <span className="mr-2 text-xs uppercase tracking-[0.2em] text-slate-400">{label}</span>
      <span>{value}</span>
    </div>
  );
}
