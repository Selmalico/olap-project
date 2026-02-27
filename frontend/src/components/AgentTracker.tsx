interface Props {
  agents?: string[];
  operations?: string[];
  loading?: boolean;
}

const AGENT_META: Record<string, { label: string; icon: string; color: string }> = {
  dimension_navigator: { label: 'Dimension Navigator', icon: '🔭', color: 'bg-violet-500/15 text-violet-700 border-violet-300' },
  cube_operations: { label: 'Cube Operations', icon: '🎲', color: 'bg-amber-500/15 text-amber-800 border-amber-300' },
  kpi_calculator: { label: 'KPI Calculator', icon: '📊', color: 'bg-emerald-500/15 text-emerald-800 border-emerald-300' },
  report_generator: { label: 'Report Generator', icon: '📋', color: 'bg-slate-500/15 text-slate-700 border-slate-300' },
  visualization_agent: { label: 'Visualization', icon: '📈', color: 'bg-blue-500/15 text-blue-800 border-blue-300' },
  anomaly_detection: { label: 'Anomaly Detection', icon: '🔍', color: 'bg-rose-500/15 text-rose-800 border-rose-300' },
  executive_summary: { label: 'Executive Summary', icon: '💼', color: 'bg-teal-500/15 text-teal-800 border-teal-300' },
};

const OPERATION_META: Record<string, { label: string; icon: string; color: string }> = {
  slice: { label: 'Slice', icon: '✂️', color: 'bg-sky-500/15 text-sky-800 border-sky-300' },
  dice: { label: 'Dice', icon: '🎲', color: 'bg-indigo-500/15 text-indigo-800 border-indigo-300' },
  drill_down: { label: 'Drill-down', icon: '⬇️', color: 'bg-violet-500/15 text-violet-700 border-violet-300' },
  roll_up: { label: 'Roll-up', icon: '⬆️', color: 'bg-purple-500/15 text-purple-700 border-purple-300' },
  pivot: { label: 'Pivot', icon: '📊', color: 'bg-amber-500/15 text-amber-800 border-amber-300' },
  yoy_growth: { label: 'YoY Growth', icon: '📈', color: 'bg-emerald-500/15 text-emerald-800 border-emerald-300' },
  mom_change: { label: 'MoM Change', icon: '📉', color: 'bg-teal-500/15 text-teal-800 border-teal-300' },
  compare_periods: { label: 'Compare', icon: '⚖️', color: 'bg-blue-500/15 text-blue-800 border-blue-300' },
  top_n: { label: 'Top N', icon: '🏆', color: 'bg-amber-500/15 text-amber-800 border-amber-300' },
  profit_margins: { label: 'Margins', icon: '💰', color: 'bg-lime-500/15 text-lime-800 border-lime-400' },
  revenue_share: { label: 'Revenue Share', icon: '🥧', color: 'bg-pink-500/15 text-pink-800 border-pink-300' },
  drill_through: { label: 'Drill-through', icon: '🔎', color: 'bg-cyan-500/15 text-cyan-800 border-cyan-300' },
  ytd_revenue:   { label: 'YTD Revenue', icon: '📅', color: 'bg-green-500/15 text-green-800 border-green-300' },
  rolling_avg:   { label: 'Rolling Avg', icon: '〰️', color: 'bg-blue-500/15 text-blue-700 border-blue-300' },
  aggregate:     { label: 'Aggregate', icon: '🔢', color: 'bg-slate-500/15 text-slate-700 border-slate-300' },
};

function getMeta(key: string, isOperation: boolean) {
  const meta = isOperation ? OPERATION_META[key] : AGENT_META[key];
  if (meta) return meta;
  const label = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  return { label, icon: '⚡', color: 'bg-slate-500/15 text-slate-700 border-slate-300' };
}

export function AgentTracker({ agents = [], operations = [], loading = false }: Props) {
  const items = operations.length ? operations : agents;
  const isOp = operations.length > 0;

  if (!loading && items.length === 0) return null;

  return (
    <div className="rounded-xl border border-slate-200/80 bg-gradient-to-r from-slate-50 to-slate-100/80 p-3 shadow-sm">
      <p className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold mb-2">
        {loading ? 'Pipeline' : 'Agents & actions'}
      </p>
      <div className="flex flex-wrap gap-2">
        {loading && (
          <span className="inline-flex items-center gap-2 text-sm text-slate-600 font-medium">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-400 border-t-transparent" />
            Routing through OLAP agents…
          </span>
        )}
        {!loading &&
          items.map((key) => {
            const meta = getMeta(key, isOp);
            return (
              <span
                key={key}
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium ${meta.color}`}
              >
                <span className="opacity-90">{meta.icon}</span>
                {meta.label}
              </span>
            );
          })}
      </div>
    </div>
  );
}
