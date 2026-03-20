import { Handle, Position } from 'reactflow';
import { formatDuration } from '../utils/formatDuration';

export default function CourseNode({ data }) {
  const { course, phase_num } = data;

  const phaseColors = {
    1: 'border-l-blue-500',
    2: 'border-l-purple-500',
    3: 'border-l-orange-500',
    4: 'border-l-slate-400'
  };

  const levelColors = {
    1: 'bg-slate-100 text-slate-600',
    2: 'bg-blue-100 text-blue-700',
    3: 'bg-purple-100 text-purple-700'
  };

  const levelLabels = { 1: 'B', 2: 'I', 3: 'A' };

  return (
    <div 
      className={`border border-slate-200 rounded-lg bg-white shadow-sm hover:shadow-md cursor-pointer transition-shadow p-2 w-[200px] h-[80px] border-l-4 ${phaseColors[phase_num] || 'border-l-slate-300'} relative flex flex-col justify-between`}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      
      <div className="flex justify-between items-start w-full">
        <h3 className="text-xs font-medium leading-tight line-clamp-2 w-[140px] text-slate-800">
          {course.title}
        </h3>
        <div className={`w-5 h-5 rounded text-[10px] font-bold flex items-center justify-center shrink-0 ${levelColors[course.level_num]}`}>
          {levelLabels[course.level_num] || course.level.charAt(0).toUpperCase()}
        </div>
      </div>

      <div className="flex justify-between items-end w-full">
        <span className="text-[10px] px-1.5 py-0.5 bg-slate-100 rounded text-slate-600 truncate max-w-[100px]" title={course.addresses_skill}>
          {course.addresses_skill}
        </span>
        <span className="text-[10px] font-medium text-slate-400">
          {formatDuration(course.duration_hrs)}
        </span>
      </div>

      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}
