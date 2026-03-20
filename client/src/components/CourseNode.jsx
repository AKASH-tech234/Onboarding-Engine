import { useState } from 'react';
import { Handle, Position } from 'reactflow';
import { formatDuration } from '../utils/formatDuration';

export default function CourseNode({ data }) {
  const { course, phase_num, phase_label } = data;
  const [isHovered, setIsHovered] = useState(false);

  const phaseColors = {
    1: '#4f8ef7',
    2: '#a78bfa',
    3: '#f59e0b',
    4: '#10b981',
  };

  const phasePillColors = {
    1: { bg: 'rgba(79,142,247,0.15)', text: '#93bbfd', border: 'rgba(79,142,247,0.25)' },
    2: { bg: 'rgba(167,139,250,0.15)', text: '#c4b5fd', border: 'rgba(167,139,250,0.25)' },
    3: { bg: 'rgba(245,158,11,0.15)', text: '#fCD34D', border: 'rgba(245,158,11,0.25)' },
    4: { bg: 'rgba(16,185,129,0.15)', text: '#6ee7b7', border: 'rgba(16,185,129,0.25)' },
  };

  const getTheme = (phase) => phaseColors[phase] || phaseColors[4];
  const getPillTheme = (phase) => phasePillColors[phase] || phasePillColors[4];

  const themeColor = getTheme(phase_num);
  const pillTheme = getPillTheme(phase_num);
  const levelLabels = { 1: 'Foundation', 2: 'Core', 3: 'Advanced' };

  return (
    <div 
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        background: isHovered ? "rgba(255,255,255,0.07)" : "rgba(255,255,255,0.04)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        border: isHovered ? "1px solid rgba(79,142,247,0.3)" : "1px solid rgba(255,255,255,0.08)",
        borderRadius: "14px",
        padding: "14px 16px",
        minWidth: "160px",
        maxWidth: "200px",
        position: "relative",
        overflow: "hidden",
        boxShadow: isHovered 
          ? "0 8px 32px rgba(79,142,247,0.12), inset 0 1px 0 rgba(255,255,255,0.1)"
          : "0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.06)",
        transform: isHovered ? "translateY(-2px)" : "translateY(0)",
        transition: "all 0.25s cubic-bezier(0.4,0,0.2,1)",
        cursor: "pointer",
        willChange: "transform"
      }}
    >
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: themeColor }} />

      <div 
        style={{
          position: "absolute", top: 0, width: "60%", height: "100%",
          background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.04), transparent)",
          transition: "left 0.6s ease-in-out",
          left: isHovered ? "200%" : "-100%",
          pointerEvents: "none"
        }}
      />

      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <span style={{
          fontSize: '9px', letterSpacing: '0.12em', textTransform: 'uppercase',
          padding: '2px 7px', borderRadius: '999px', fontWeight: 500,
          background: pillTheme.bg, color: pillTheme.text, border: `1px solid ${pillTheme.border}`
        }}>
          {phase_label || `Phase ${phase_num}`}
        </span>
        <span style={{
          fontSize: '9px', letterSpacing: '0.12em', textTransform: 'uppercase',
          padding: '2px 7px', borderRadius: '999px', fontWeight: 500,
          background: pillTheme.bg, color: pillTheme.text, border: `1px solid ${pillTheme.border}`,
          opacity: 0.7
        }}>
          {levelLabels[course.level_num] || course.level || 'Optional'}
        </span>
      </div>

      <h3 style={{ fontSize: '13px', fontWeight: 500, color: '#f0f2f5', lineHeight: 1.4, marginBottom: '10px' }} className="line-clamp-2">
        {course.title}
      </h3>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: themeColor, flexShrink: 0 }} />
          <span style={{ fontSize: '11px', color: '#6b7280', fontFamily: "'DM Mono', monospace", maxWidth: '100px' }} className="truncate" title={course.addresses_skill}>
            {course.addresses_skill}
          </span>
        </div>
        <span style={{ fontSize: '11px', color: '#6b7280', fontFamily: "'DM Mono', monospace" }}>
          {formatDuration(course.duration_hrs)}
        </span>
      </div>

      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}
