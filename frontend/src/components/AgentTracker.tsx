interface Props {
  agents: string[];
  loading: boolean;
}

const AGENT_META: Record<string, { label: string; icon: string }> = {
  dimension_navigator:  { label: 'Dimension Navigator',  icon: '🔭' },
  cube_operations:      { label: 'Cube Operations',      icon: '🎲' },
  kpi_calculator:       { label: 'KPI Calculator',       icon: '📊' },
  report_generator:     { label: 'Report Generator',     icon: '📋' },
  visualization_agent:  { label: 'Visualization',        icon: '📈' },
  anomaly_detection:    { label: 'Anomaly Detection',    icon: '🔍' },
  executive_summary:    { label: 'Executive Summary',    icon: '💼' },
};

export function AgentTracker({ agents, loading }: Props) {
  if (!loading && agents.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2 p-3 bg-blue-50 rounded-lg border border-blue-100 my-2">
      {loading && (
        <span className="flex items-center gap-1.5 text-sm text-blue-700 font-medium">
          <span className="animate-spin">&#9881;</span> Routing query through agents...
        </span>
      )}
      {agents.map(a => {
        const meta = AGENT_META[a] || { label: a, icon: '🤖' };
        return (
          <span key={a}
            className="inline-flex items-center gap-1 px-2.5 py-1 bg-white
                       text-blue-800 text-xs font-medium border border-blue-200
                       rounded-full shadow-sm">
            {meta.icon} {meta.label}
          </span>
        );
      })}
    </div>
  );
}
