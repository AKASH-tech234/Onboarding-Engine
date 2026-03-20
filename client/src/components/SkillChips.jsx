export default function SkillChips({ items }) {
  if (!items || items.length === 0) {
    return <span className="text-xs italic text-slate-500">No items yet</span>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item, i) => (
        <div
          key={i}
          title={`${item.current || 'none'} -> ${item.target || 'any'}`}
          className="group relative inline-flex cursor-help items-center gap-2 rounded-full border border-teal-500/20 bg-teal-900/30 px-3 py-1.5 text-xs font-medium tracking-wide text-teal-100 transition-all will-change-transform duration-300 hover:border-green-400/50 hover:drop-shadow-[0_0_15px_rgba(74,222,128,0.2)] overflow-hidden"
        >
          {/* Shimmer effect */}
          <div className="absolute inset-0 z-0 -translate-x-[150%] animate-[shimmer_3s_infinite_linear] bg-gradient-to-r from-transparent via-white/10 to-transparent bg-[length:200%_100%]" />
          
          <span className="relative z-10 h-1.5 w-1.5 rounded-full bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.8)]" />
          <span className="relative z-10">Assumed skill</span>
        </div>
      ))}
    </div>
  );
}
