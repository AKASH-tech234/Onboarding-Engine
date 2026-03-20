export default function SkillChips({ items, color }) {
  if (!items || items.length === 0) return <span className="text-slate-400 text-xs italic">None</span>;

  const colorClasses = {
    green: 'bg-green-100 text-green-800 border-green-200',
    red: 'bg-red-100 text-red-800 border-red-200',
    amber: 'bg-amber-100 text-amber-800 border-amber-200',
  };

  const className = colorClasses[color] || colorClasses.green;

  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, i) => (
        <span
          key={i}
          className={`inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-medium cursor-help transition-colors ${className}`}
          title={`${item.current || 'none'} → ${item.target || 'any'}`}
        >
          {item.skill}
        </span>
      ))}
    </div>
  );
}
