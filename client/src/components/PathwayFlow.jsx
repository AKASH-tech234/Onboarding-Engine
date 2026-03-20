import React, { useCallback } from 'react';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import dagre from '@dagrejs/dagre';
import CourseNode from './CourseNode';
import 'reactflow/dist/style.css';

const NODE_WIDTH = 200;
const NODE_HEIGHT = 80;

const getLayoutedElements = (nodes, edges) => {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'TB', ranksep: 80, nodesep: 40 });

  nodes.forEach(n => g.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT }));
  edges.forEach(e => g.setEdge(e.source, e.target));

  dagre.layout(g);

  return {
    nodes: nodes.map(n => {
      const { x, y } = g.node(n.id);
      return { ...n, position: { x: x - NODE_WIDTH / 2, y: y - NODE_HEIGHT / 2 } };
    }),
    edges
  };
};

const nodeTypes = { courseNode: CourseNode };

export default function PathwayFlow({ pathway, onNodeClick }) {
  if (!pathway?.phases || pathway.phases.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="text-green-500 text-5xl mb-4">✓</div>
          <h2 className="text-xl font-semibold text-slate-800">No Pathway Required</h2>
          <p className="text-slate-500 mt-2">This candidate meets all requirements.</p>
        </div>
      </div>
    );
  }

  const rawNodes = pathway.phases.flatMap(phase =>
    phase.courses.map(course => ({
      id: course.id,
      type: 'courseNode',
      position: { x: 0, y: 0 },
      data: { course, phase_label: phase.phase_label, phase_num: phase.phase }
    }))
  );

  const rawEdges = pathway.phases.flatMap(phase =>
    phase.courses.flatMap(course =>
      (course.prerequisites || []).map(prereqId => ({
        id: `${prereqId}-${course.id}`,
        source: prereqId,
        target: course.id,
        animated: true,
        type: 'smoothstep'
      }))
    )
  );

  const { nodes, edges } = getLayoutedElements(rawNodes, rawEdges);

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        nodesDraggable={false}
        onNodeClick={(_, node) => onNodeClick(node.id)}
      >
        <Background variant="dots" gap={16} color="#e2e8f0" />
        <Controls />
        <MiniMap className="hidden sm:block" />
      </ReactFlow>
    </div>
  );
}
