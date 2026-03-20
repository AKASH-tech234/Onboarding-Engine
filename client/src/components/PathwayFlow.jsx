import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
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

const nodeTypes = { courseNode: CourseNode };
const phaseTheme = {
  1: 'Foundation',
  2: 'Core Competency',
  3: 'Specialization',
  4: 'Stretch Goals',
};

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

  const rawNodes = pathway.phases.flatMap((phase) =>
    phase.courses.map((course) => ({
      id: course.id,
      type: 'courseNode',
      position: { x: 0, y: 0 },
      data: { course, phase_label: phase.phase_label, phase_num: phase.phase },
    }))
  );

  const rawEdges = pathway.phases.flatMap((phase) =>
    phase.courses.flatMap((course) =>
      (course.prerequisites || []).map((prereqId) => ({
        id: `${prereqId}-${course.id}`,
        source: prereqId,
        target: course.id,
        animated: true,
        type: 'smoothstep',
      }))
    )
  );

  const { nodes, edges } = getLayoutedElements(rawNodes, rawEdges);
  const totalCourses = pathway.phases.reduce((sum, phase) => sum + phase.courses.length, 0);

  return (
    <div className="relative h-full w-full overflow-hidden rounded-[32px] border border-white/10 bg-slate-950/35 shadow-[0_30px_80px_rgba(2,6,23,0.45)]">
      <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-slate-950/55 px-5 py-4 backdrop-blur-xl">
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

      <div className="absolute left-5 top-24 z-10 hidden max-w-xs rounded-2xl border border-white/10 bg-slate-950/55 p-4 text-xs text-slate-300 backdrop-blur-xl xl:block">
        <p className="font-semibold uppercase tracking-[0.22em] text-slate-400">How to read</p>
        <p className="mt-2 leading-6 text-slate-300">
          Courses are ordered by prerequisite dependencies and weighted priority. Click any card to inspect its recommendation score and prerequisite chain.
        </p>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges.map((edge) => ({
          ...edge,
          type: 'smoothstep',
          animated: true,
          style: { stroke: 'rgba(148,163,184,0.65)', strokeWidth: 2 },
        }))}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.35}
        maxZoom={1.4}
        nodesDraggable={false}
        panOnScroll
        selectionOnDrag={false}
        onNodeClick={(_, node) => onNodeClick(node.id)}
      >
        <Background variant="dots" gap={18} size={1.2} color="rgba(148, 163, 184, 0.18)" />
        <Controls showInteractive={false} />
        <MiniMap className="hidden sm:block" nodeColor={() => '#7c8cff'} maskColor="rgba(2,6,23,0.55)" />
      </ReactFlow>

      <div className="pointer-events-none absolute bottom-5 left-5 z-10 flex flex-wrap gap-2">
        {pathway.phases.map((phase) => (
          <span key={phase.phase} className="rounded-full border border-white/10 bg-slate-950/50 px-3 py-1.5 text-xs font-semibold text-slate-200 backdrop-blur-xl">
            {phaseTheme[phase.phase] || phase.phase_label}
          </span>
        ))}
      </div>
    </div>
  );
}

function InfoPill({ label, value }) {
  return (
    <div className="rounded-full border border-white/10 bg-white/6 px-3 py-1.5 text-xs font-semibold text-slate-100">
      <span className="mr-2 text-slate-400">{label}</span>
      <span>{value}</span>
    </div>
  );
}
