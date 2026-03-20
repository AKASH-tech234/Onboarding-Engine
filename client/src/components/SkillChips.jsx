export default function SkillChips({ items, color }) {
  if (!items || items.length === 0) {
    return <span className="text-xs italic text-slate-500">No items yet</span>;
  }

  const colorClasses = {
    green: 'border-emerald-400/20 bg-emerald-400/10 text-emerald-100',
    red: 'border-rose-400/20 bg-rose-400/10 text-rose-100',
    amber: 'border-amber-400/20 bg-amber-400/10 text-amber-100',
  };

  const className = colorClasses[color] || colorClasses.green;

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item, i) => (
        <span
          key={i}
          className={`inline-flex cursor-help items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold tracking-wide transition-transform duration-200 hover:-translate-y-0.5 ${className}`}
          title={`${item.current || 'none'} -> ${item.target || 'any'}`}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-current opacity-80" />
          {item.skill}
        </span>
      ))}
    </div>
  );
}
