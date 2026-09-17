import type { KGNodeType, KnowledgeGraph } from "@/lib/types";

const COLUMN_ORDER: KGNodeType[] = ["topic", "document", "entity", "correction"];
const COLUMN_COLOR: Record<KGNodeType, string> = {
  topic: "var(--accent)",
  document: "var(--accent-2)",
  entity: "var(--text-dim)",
  correction: "var(--danger)",
};

const COL_WIDTH = 190;
const ROW_HEIGHT = 54;
const NODE_WIDTH = 168;

export function KnowledgeGraphView({ graph }: { graph: KnowledgeGraph }) {
  if (graph.nodes.length === 0) {
    return <p className="font-body text-sm text-text-dim">No knowledge graph attached to this answer.</p>;
  }

  const columns = COLUMN_ORDER.map((type) => ({
    type,
    nodes: graph.nodes.filter((n) => n.type === type),
  })).filter((col) => col.nodes.length > 0);

  const width = columns.length * COL_WIDTH;
  const rowCount = Math.max(...columns.map((c) => c.nodes.length), 1);
  const height = rowCount * ROW_HEIGHT + 24;

  const positions = new Map<string, { x: number; y: number }>();
  columns.forEach((col, colIdx) => {
    col.nodes.forEach((node, rowIdx) => {
      positions.set(node.id, {
        x: colIdx * COL_WIDTH + COL_WIDTH / 2,
        y: rowIdx * ROW_HEIGHT + ROW_HEIGHT / 2 + 12,
      });
    });
  });

  return (
    <div className="overflow-x-auto rounded-md border border-border bg-surface p-4">
      <svg width={width} height={height} role="img" aria-label="Knowledge graph used for this answer">
        {graph.edges.map((edge, i) => {
          const from = positions.get(edge.source);
          const to = positions.get(edge.target);
          if (!from || !to) return null;
          return (
            <g key={`${edge.source}-${edge.target}-${i}`}>
              <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="var(--border)" strokeWidth={1.5} />
              <text
                x={(from.x + to.x) / 2}
                y={(from.y + to.y) / 2 - 4}
                textAnchor="middle"
                fontSize="9"
                fill="var(--text-dim)"
                fontFamily="var(--font-mono)"
              >
                {edge.relation}
              </text>
            </g>
          );
        })}
        {columns.map((col) =>
          col.nodes.map((node) => {
            const pos = positions.get(node.id)!;
            return (
              <g key={node.id}>
                <rect
                  x={pos.x - NODE_WIDTH / 2}
                  y={pos.y - 16}
                  width={NODE_WIDTH}
                  height={32}
                  rx={8}
                  fill="var(--surface)"
                  stroke={COLUMN_COLOR[node.type]}
                  strokeWidth={1.5}
                />
                <text
                  x={pos.x}
                  y={pos.y + 4}
                  textAnchor="middle"
                  fontSize="10.5"
                  fill="var(--text)"
                  fontFamily="var(--font-body)"
                >
                  {node.label.length > 24 ? `${node.label.slice(0, 22)}…` : node.label}
                </text>
              </g>
            );
          })
        )}
      </svg>
    </div>
  );
}
