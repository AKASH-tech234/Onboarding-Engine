import { Handle, Position } from 'reactflow';
import { formatDuration } from '../utils/formatDuration';

export default function CourseNode({ data }) {
  const { course, phase_num } = data;

  const phaseColors = {
    1: 'from-cyan-400/25 to-sky-500/10 border-cyan-300/30',
    2: 'from-indigo-400/25 to-violet-500/10 border-indigo-300/30',
    3: 'from-amber-400/25 to-orange-500/10 border-amber-300/30',
    4: 'from-slate-400/20 to-slate-500/10 border-slate-300/20',
  };

  const levelColors = {
    1: 'border-cyan-300/20 bg-cyan-400/12 text-cyan-100',
    2: 'border-indigo-300/20 bg-indigo-400/12 text-indigo-100',
    3: 'border-amber-300/20 bg-amber-400/12 text-amber-100',
  };

  const levelLabels = { 1: 'Foundation', 2: 'Core', 3: 'Advanced' };
  const phaseClass = phaseColors[phase_num] || phaseColors[1];

  return (
    <div className={`relative flex h-[126px] w-[244px] cursor-pointer flex-col justify-between overflow-hidden rounded-[26px] border bg-gradient-to-br p-4 text-white shadow-[0_18px_45px_rgba(2,6,23,0.35)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_24px_55px_rgba(15,23,42,0.42)] ${phaseClass}`}>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.12),transparent_42%)]" />
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />

      <div className="relative flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] uppercase tracking-[0.24em] text-slate-400">Phase {phase_num}</p>
          <h3 className="mt-2 line-clamp-2 text-sm font-semibold leading-tight text-slate-50">
            {course.title}
          </h3>
        </div>
        <div className={`rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${levelColors[course.level_num]}`}>
          {levelLabels[course.level_num] || course.level}
        </div>
      </div>

      <div className="relative flex items-end justify-between gap-3">
        <div className="min-w-0">
          <div className="inline-flex max-w-[128px] items-center gap-2 rounded-full border border-white/10 bg-white/6 px-3 py-1 text-[11px] font-medium text-slate-200">
            <span className="h-2 w-2 rounded-full bg-cyan-300 shadow-[0_0_10px_rgba(103,232,249,0.8)]" />
            <span className="truncate" title={course.addresses_skill}>{course.addresses_skill}</span>
          </div>
        </div>
        <span className="text-xs font-semibold text-slate-300">
          {formatDuration(course.duration_hrs)}
        </span>
      </div>

      <div className="pointer-events-none absolute inset-x-4 bottom-0 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent" />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}
