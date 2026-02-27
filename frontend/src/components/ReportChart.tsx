import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

const CHART_COLORS = [
  '#2E75B6',
  '#00B0F0',
  '#1F7A4D',
  '#C55A11',
  '#5B2D8E',
  '#06b6d4',
  '#f59e0b',
  '#ef4444',
];

interface ReportChartProps {
  report: {
    rows?: Record<string, unknown>[];
    columns?: string[];
    columns_list?: string[];
    rows_list?: Record<string, unknown>[];
    operation?: string;
  };
  height?: number;
  className?: string;
}

export function ReportChart({ report, height = 240, className = '' }: ReportChartProps) {
  const rows = report.rows_list?.length ? report.rows_list : report.rows;
  const cols = report.columns_list?.length ? report.columns_list : report.columns || (rows?.[0] ? Object.keys(rows[0]) : []);

  if (!rows?.length || !cols?.length) return null;

  const labelCol = cols.find(
    (c) =>
      typeof (rows[0] as Record<string, unknown>)[c] === 'string' ||
      c.includes('group') ||
      c.includes('year') ||
      c.includes('month') ||
      c.includes('name') ||
      c === 'row_dim'
  );
  const metricCols = cols.filter(
    (c) =>
      c !== labelCol &&
      !c.includes('count') &&
      !c.includes('rank') &&
      !c.includes('_totals') &&
      rows.some((r) => {
        const v = (r as Record<string, unknown>)[c];
        return typeof v === 'number' || (typeof v === 'string' && !isNaN(parseFloat(v as string)));
      })
  );

  if (!labelCol || !metricCols.length) return null;

  const chartData = rows.slice(0, 24).map((r) => {
    const entry: Record<string, string | number> = { name: String((r as Record<string, unknown>)[labelCol] ?? '') };
    metricCols.forEach((m) => {
      const v = (r as Record<string, unknown>)[m];
      entry[m] =
        typeof v === 'number' ? v : parseFloat(String(v).replace(/[$,%+]/g, '')) || 0;
    });
    return entry;
  });

  const op = report.operation || '';
  const isTimeSeries =
    labelCol.includes('month') ||
    labelCol.includes('year') ||
    (labelCol === 'name' && chartData[0]?.name?.match(/^\d{4}$/));
  const isPie =
    metricCols.length === 1 && chartData.length <= 10 && (op.includes('share') || op.includes('revenue_share'));

  const tooltipStyle = {
    background: 'rgba(30, 41, 59, 0.98)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 10,
    fontSize: 12,
    padding: '10px 14px',
  };

  if (isPie) {
    return (
      <div className={className}>
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <Pie
              data={chartData}
              dataKey={metricCols[0]}
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={Math.min(80, height * 0.35)}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            >
              {chartData.map((_, i) => (
                <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} stroke="rgba(255,255,255,0.1)" strokeWidth={1} />
              ))}
            </Pie>
            <Tooltip formatter={(v: number) => v?.toLocaleString?.()} contentStyle={tooltipStyle} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (isTimeSeries) {
    return (
      <div className={className}>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.2)" />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} />
            <YAxis
              tick={{ fontSize: 11, fill: '#64748b' }}
              tickFormatter={(v) =>
                v >= 1_000_000 ? `${(v / 1_000_000).toFixed(1)}M` : v >= 1000 ? `${(v / 1000).toFixed(0)}K` : v
              }
            />
            <Tooltip formatter={(v: number) => v?.toLocaleString?.()} contentStyle={tooltipStyle} />
            {metricCols.slice(0, 4).map((m, i) => (
              <Line
                key={m}
                type="monotone"
                dataKey={m}
                stroke={CHART_COLORS[i]}
                dot={false}
                strokeWidth={2}
                name={m.replace(/_/g, ' ')}
              />
            ))}
            <Legend />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={chartData} margin={{ top: 8, right: 16, bottom: 24, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.2)" />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 10, fill: '#64748b' }}
            angle={-35}
            textAnchor="end"
            interval={0}
            height={56}
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#64748b' }}
            tickFormatter={(v) =>
              v >= 1_000_000 ? `${(v / 1_000_000).toFixed(1)}M` : v >= 1000 ? `${(v / 1000).toFixed(0)}K` : v
            }
          />
          <Tooltip formatter={(v: number) => v?.toLocaleString?.()} contentStyle={tooltipStyle} />
          {metricCols.slice(0, 4).map((m, i) => (
            <Bar key={m} dataKey={m} fill={CHART_COLORS[i]} radius={[4, 4, 0, 0]} name={m.replace(/_/g, ' ')} />
          ))}
          <Legend />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
