import { useNavigate } from 'react-router-dom';

const DEMO_SESSIONS = { tech: 'FILL_AFTER_DEPLOY', ops: 'FILL_AFTER_DEPLOY' };

export default function ExampleBadge() {
  const navigate = useNavigate();

  return (
    <div className="flex items-center gap-3 mt-4 text-sm text-slate-500 justify-center">
      or try a sample →
      <button
        disabled={DEMO_SESSIONS.tech === 'FILL_AFTER_DEPLOY'}
        onClick={() => navigate('/results/' + DEMO_SESSIONS.tech)}
        className="inline-flex items-center px-3 py-1 bg-slate-100 hover:bg-slate-200 rounded-full cursor-pointer disabled:opacity-40 transition-colors"
        title={DEMO_SESSIONS.tech === 'FILL_AFTER_DEPLOY' ? 'Available after deployment' : ''}
      >
        💼 Tech Role
      </button>
      <button
        disabled={DEMO_SESSIONS.ops === 'FILL_AFTER_DEPLOY'}
        onClick={() => navigate('/results/' + DEMO_SESSIONS.ops)}
        className="inline-flex items-center px-3 py-1 bg-slate-100 hover:bg-slate-200 rounded-full cursor-pointer disabled:opacity-40 transition-colors"
        title={DEMO_SESSIONS.ops === 'FILL_AFTER_DEPLOY' ? 'Available after deployment' : ''}
      >
        🏭 Ops Role
      </button>
    </div>
  );
}
