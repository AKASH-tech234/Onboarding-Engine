export default function AnalyzeButton({ disabled, loading, onClick }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`group relative w-full overflow-hidden rounded-2xl border border-white/15 px-5 py-4 text-sm font-semibold tracking-wide text-white transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-300/60 ${
        disabled || loading
          ? 'cursor-not-allowed bg-slate-700/60 opacity-60'
          : 'bg-gradient-to-r from-indigo-500 via-indigo-400 to-cyan-400 shadow-[0_16px_35px_rgba(99,102,241,0.35)] hover:-translate-y-0.5 hover:shadow-[0_22px_45px_rgba(56,189,248,0.28)]'
      }`}
    >
      <span className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.28),transparent_48%)] opacity-80" />
      {loading ? (
        <span className="relative z-10 flex items-center justify-center">
          <svg className="mr-3 h-5 w-5 animate-spin text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Building your pathway...
        </span>
      ) : (
        <span className="relative z-10 flex items-center justify-center gap-2">
          Generate adaptive pathway
          <span className="transition-transform duration-300 group-hover:translate-x-1">→</span>
        </span>
      )}
    </button>
  );
}
