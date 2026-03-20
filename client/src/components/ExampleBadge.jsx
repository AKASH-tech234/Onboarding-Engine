import { useNavigate } from 'react-router-dom';

const DEMO_SESSIONS = { tech: 'FILL_AFTER_DEPLOY', ops: 'FILL_AFTER_DEPLOY' };

export default function ExampleBadge() {
  const navigate = useNavigate();

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs uppercase tracking-[0.24em] text-slate-400">
          Demo sessions
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            disabled={DEMO_SESSIONS.tech === 'FILL_AFTER_DEPLOY'}
            onClick={() => navigate('/results/' + DEMO_SESSIONS.tech)}
            className="rounded-full border border-indigo-300/20 bg-indigo-400/10 px-3 py-1.5 text-xs font-semibold text-indigo-100 transition-all duration-300 hover:border-indigo-200/40 hover:bg-indigo-400/20 disabled:cursor-not-allowed disabled:opacity-40"
            title={DEMO_SESSIONS.tech === 'FILL_AFTER_DEPLOY' ? 'Available after deployment' : ''}
          >
            Tech role
          </button>
          <button
            disabled={DEMO_SESSIONS.ops === 'FILL_AFTER_DEPLOY'}
            onClick={() => navigate('/results/' + DEMO_SESSIONS.ops)}
            className="rounded-full border border-cyan-300/20 bg-cyan-400/10 px-3 py-1.5 text-xs font-semibold text-cyan-100 transition-all duration-300 hover:border-cyan-200/40 hover:bg-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-40"
            title={DEMO_SESSIONS.ops === 'FILL_AFTER_DEPLOY' ? 'Available after deployment' : ''}
          >
            Ops role
          </button>
        </div>
      </div>
    </div>
  );
}
