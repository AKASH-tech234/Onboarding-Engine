import React, { useState } from 'react';
import ReactFlow, { Background, Controls, MiniMap, getBezierPath } from 'reactflow';
import dagre from '@dagrejs/dagre';
import CourseNode from './CourseNode';
import 'reactflow/dist/style.css';

const NODE_WIDTH = 244;
const NODE_HEIGHT = 126;

const getLayoutedElements = (nodes, edges) => {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'TB', ranksep: 100, nodesep: 56 });

  nodes.forEach((node) => g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT }));
  edges.forEach((edge) => g.setEdge(edge.source, edge.target));

  dagre.layout(g);

  return {
    nodes: nodes.map((node) => {
      const { x, y } = g.node(node.id);
      return { ...node, position: { x: x - NODE_WIDTH / 2, y: y - NODE_HEIGHT / 2 } };
    }),
    edges,
  };
};

const FlowingEdge = ({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition }) => {
  const [edgePath] = getBezierPath({ sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition });
  const [isHovered, setIsHovered] = useState(false);

  return (
    <>
      <path
        id={`edge-path-${id}`}
        d={edgePath}
        fill="none"
        stroke={isHovered ? "rgba(79,142,247,0.6)" : "rgba(99,102,241,0.25)"}
        strokeWidth={isHovered ? 2 : 1.5}
        strokeDasharray="none"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        markerEnd="url(#flowArrow)"
        style={{
          transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
          willChange: "stroke, stroke-width"
        }}
      />
      <path
        d={edgePath}
        fill="none"
        stroke="transparent"
        strokeWidth={15}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      />
      <circle r="2.5" fill="#4f8ef7" opacity="0.8">
        <animateMotion dur="2s" repeatCount="indefinite">
          <mpath href={`#edge-path-${id}`} />
        </animateMotion>
      </circle>
    </>
  );
};

const nodeTypes = { courseNode: CourseNode };
const edgeTypes = { flowingEdge: FlowingEdge };

const phaseTheme = {
  1: 'Foundation',
  2: 'Core Competency',
  3: 'Specialization',
  4: 'Stretch Goals',
};

function InfoPill({ label, value }) {
  return (
    <div style={{
      background: "rgba(255,255,255,0.04)",
      border: "1px solid rgba(255,255,255,0.08)",
      borderRadius: "999px",
      padding: "6px 14px",
      fontSize: "13px",
      color: "#9ca3af",
      fontWeight: 400
    }}>
      {label}
      <span style={{ color: "#f0f2f5", fontWeight: 600, fontFamily: "'DM Mono', monospace", marginLeft: "6px" }}>
        {value}
      </span>
    </div>
  );
}

export default function PathwayFlow({ pathway, onNodeClick }) {
  if (!pathway?.phases || pathway.phases.length === 0) {
    return (
      <div className="flex h-full w-full items-center justify-center rounded-[32px] border border-white/10 bg-white/6">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-emerald-300/20 bg-emerald-400/10 text-2xl text-emerald-200">✓</div>
          <h2 className="text-xl font-semibold text-slate-50">No pathway required</h2>
          <p className="mt-2 text-slate-400">This candidate already meets the target role requirements.</p>
        </div>
      </div>
    );
  }

  const { nodes, edges } = React.useMemo(() => {
    const rNodes = pathway.phases.flatMap((phase) =>
      phase.courses.map((course) => ({
        id: course.id,
        type: 'courseNode',
        position: { x: 0, y: 0 },
        data: { course, phase_label: phase.phase_label, phase_num: phase.phase },
      }))
    );

    const rEdges = pathway.phases.flatMap((phase) =>
      phase.courses.flatMap((course) =>
        (course.prerequisites || []).map((prereqId) => ({
          id: `${prereqId}-${course.id}`,
          source: prereqId,
          target: course.id,
          animated: false,
          type: 'flowingEdge',
        }))
      )
    );

    const nodeIds = new Set(rNodes.map(n => n.id));
    const vEdges = rEdges.filter(edge => nodeIds.has(edge.source) && nodeIds.has(edge.target));

    return getLayoutedElements(rNodes, vEdges);
  }, [pathway]);
  const totalCourses = pathway.phases.reduce((sum, phase) => sum + phase.courses.length, 0);

  return (
    <div 
      className="relative h-full w-full overflow-hidden shadow-2xl"
      style={{
        background: "#0a0c10",
        borderRadius: "16px",
        border: "1px solid rgba(255,255,255,0.06)"
      }}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex flex-wrap items-center justify-between gap-3 border-b border-[#ffffff0e] px-5 py-4" style={{ background: "rgba(10, 12, 16, 0.55)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)" }}>
        <div>
          <p className="text-[11px] uppercase tracking-[0.28em] text-slate-400">Learning graph</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-50">Adaptive course pathway</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          <InfoPill label="Phases" value={pathway.phases.length} />
          <InfoPill label="Courses" value={totalCourses} />
          <InfoPill label="Hours" value={pathway.total_training_hrs || 0} />
        </div>
      </div>

      <div className="absolute left-5 top-24 z-10 hidden max-w-xs rounded-2xl border border-white/10 bg-slate-950/55 p-4 text-xs text-slate-300 xl:block" style={{ backdropFilter: "blur(8px)" }}>
        <p className="font-semibold uppercase tracking-[0.22em] text-slate-400">How to read</p>
        <p className="mt-2 leading-6 text-slate-300">
          Courses are ordered by prerequisite dependencies and weighted priority. Click any card to inspect its recommendation score and prerequisite chain.
        </p>
      </div>

      <svg style={{ position: 'absolute', top: 0, left: 0, width: 0, height: 0 }}>
        <defs>
          <marker id="flowArrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="rgba(99,102,241,0.5)"/>
          </marker>
        </defs>
      </svg>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.35}
        maxZoom={1.4}
        nodesDraggable={false}
        panOnScroll
        selectionOnDrag={false}
        onInit={(instance) => setTimeout(() => instance.fitView({ padding: 0.2, duration: 800 }), 150)}
        onNodeClick={(_, node) => onNodeClick(node.id)}
        connectionLineStyle={{ stroke: "#4f8ef7", strokeWidth: 1.5 }}
        defaultEdgeOptions={{ type: "flowingEdge", animated: false }}
      >
        <Background variant="dots" gap={24} size={1} color="rgba(255,255,255,0.06)" />
        
        <Controls 
          showInteractive={false} 
          style={{
            background: "rgba(17,19,24,0.9)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "10px",
            backdropFilter: "blur(8px)",
            boxShadow: "0 4px 16px rgba(0,0,0,0.3)"
          }}
        />

        <MiniMap 
          className="hidden sm:block"
          nodeColor={(node) => {
            const phase = node.data?.phase_num || 1;
            if (phase === 1) return "rgba(79,142,247,0.6)";
            if (phase === 2) return "rgba(167,139,250,0.6)";
            if (phase === 3) return "rgba(245,158,11,0.6)";
            return "rgba(16,185,129,0.6)";
          }}
          maskColor="rgba(0,0,0,0.6)"
          style={{
            background: "rgba(17,19,24,0.9)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "12px",
            backdropFilter: "blur(8px)",
          }}
          nodeStrokeWidth={0}
          pannable
          zoomable
        />
      </ReactFlow>

      <div className="pointer-events-none absolute bottom-5 left-[70px] z-10 flex flex-wrap gap-2">
        {pathway.phases.map((phase) => {
          const phasePillColors = {
            1: { bg: 'rgba(79,142,247,0.15)', text: '#93bbfd', border: 'rgba(79,142,247,0.25)' },
            2: { bg: 'rgba(167,139,250,0.15)', text: '#c4b5fd', border: 'rgba(167,139,250,0.25)' },
            3: { bg: 'rgba(245,158,11,0.15)', text: '#fcd34d', border: 'rgba(245,158,11,0.25)' },
            4: { bg: 'rgba(16,185,129,0.15)', text: '#6ee7b7', border: 'rgba(16,185,129,0.25)' },
          };
          const theme = phasePillColors[phase.phase] || { bg: 'rgba(255,255,255,0.04)', text: '#e2e8f0', border: 'rgba(255,255,255,0.08)' };
          
          return (
            <span key={phase.phase} 
              style={{ 
                background: theme.bg, 
                border: `1px solid ${theme.border}`, 
                color: theme.text,
                backdropFilter: "blur(8px)" 
              }} 
              className="rounded-full px-3 py-1.5 text-xs font-semibold shadow-[0_2px_8px_rgba(0,0,0,0.2)]">
              {phaseTheme[phase.phase] || phase.phase_label}
            </span>
          );
        })}
      </div>
    </div>
  );
}
