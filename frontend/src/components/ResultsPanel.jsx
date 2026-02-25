import { X, Lightbulb, AlertTriangle, BarChart2 } from 'lucide-react'
import DataTable from './DataTable'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, Legend,
} from 'recharts'

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

function tryChart(report) {
  if (!report?.rows?.length) return null
  const rows = report.rows
  const cols = report.columns || Object.keys(rows[0] || {})

  // Find the best dimension label column (first non-numeric)
  const labelCol = cols.find(c => typeof rows[0][c] === 'string' || c.includes('group') || c.includes('year') || c.includes('month') || c.includes('name'))
  const metricCols = cols.filter(c => c !== labelCol && !c.includes('count') && !c.includes('rank') && !c.includes('_totals') &&
    rows.some(r => typeof r[c] === 'number' || (typeof r[c] === 'string' && !isNaN(parseFloat(r[c])))))

  if (!labelCol || !metricCols.length) return null

  // Normalise to numbers
  const chartData = rows.slice(0, 20).map(r => {
    const entry = { name: String(r[labelCol] ?? '') }
    metricCols.forEach(m => {
      const v = r[m]
      entry[m] = typeof v === 'number' ? v : parseFloat(String(v).replace(/[$,%+]/g, '')) || 0
    })
    return entry
  })

  const op = report.operation || ''
  const isTimeSeries = labelCol.includes('month') || labelCol.includes('year') || labelCol === 'name' && chartData[0]?.name?.match(/^\d{4}$/)
  const isPie = metricCols.length === 1 && chartData.length <= 8 && op.includes('share')

  if (isPie) {
    return (
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie data={chartData} dataKey={metricCols[0]} nameKey="name" cx="50%" cy="50%" outerRadius={70}>
            {chartData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
          </Pie>
          <Tooltip formatter={v => v.toLocaleString()} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    )
  }

  if (isTimeSeries) {
    return (
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} />
          <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} tickFormatter={v => v >= 1_000_000 ? `${(v/1_000_000).toFixed(1)}M` : v >= 1000 ? `${(v/1000).toFixed(0)}K` : v} />
          <Tooltip formatter={v => v.toLocaleString()} contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} />
          {metricCols.map((m, i) => <Line key={m} type="monotone" dataKey={m} stroke={CHART_COLORS[i]} dot={false} strokeWidth={2} />)}
        </LineChart>
      </ResponsiveContainer>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData} margin={{ top: 5, right: 10, bottom: 20, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} angle={-25} textAnchor="end" interval={0} />
        <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} tickFormatter={v => v >= 1_000_000 ? `${(v/1_000_000).toFixed(1)}M` : v >= 1000 ? `${(v/1000).toFixed(0)}K` : v} />
        <Tooltip formatter={v => v.toLocaleString()} contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} />
        {metricCols.slice(0, 3).map((m, i) => <Bar key={m} dataKey={m} fill={CHART_COLORS[i]} radius={[4, 4, 0, 0]} />)}
      </BarChart>
    </ResponsiveContainer>
  )
}

export default function ResultsPanel({ result, onClose }) {
  if (!result) return null

  const reports = result.reports || []
  const summary = result.summary || {}

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-white/10 shrink-0">
        <div className="flex items-center gap-2">
          <BarChart2 size={15} className="text-brand-400" />
          <h2 className="text-sm font-semibold text-white">Analysis Results</h2>
          {!result.llm_used && (
            <span className="text-[10px] bg-yellow-500/15 text-yellow-400 border border-yellow-500/20 px-2 py-0.5 rounded-full">keyword mode</span>
          )}
          {result.llm_used && (
            <span className="text-[10px] bg-brand-500/15 text-brand-400 border border-brand-500/20 px-2 py-0.5 rounded-full capitalize">
              AI mode {result.provider ? `(${result.provider})` : ''}
            </span>
          )}
        </div>
        <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors p-1 rounded-lg hover:bg-white/5">
          <X size={15} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {/* Summary */}
        {summary.text && (
          <div className="bg-white/5 border border-white/10 rounded-xl p-4 space-y-3">
            <p className="text-sm text-slate-300 leading-relaxed">{summary.text}</p>
            {summary.highlights?.length > 0 && (
              <div className="space-y-1">
                {summary.highlights.map((h, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-emerald-400">
                    <span className="mt-0.5">•</span>{h}
                  </div>
                ))}
              </div>
            )}
            {summary.recommendations?.length > 0 && (
              <div className="border-t border-white/10 pt-3 space-y-1">
                {summary.recommendations.map((r, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-amber-400">
                    <AlertTriangle size={11} className="mt-0.5 shrink-0" />
                    {r}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Reports */}
        {reports.map((report, i) => (
          <div key={i} className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-200">{report.title}</h3>

            {/* Chart */}
            {(() => {
              const chart = tryChart(report)
              return chart ? (
                <div className="bg-white/5 border border-white/10 rounded-xl p-3">
                  {chart}
                </div>
              ) : null
            })()}

            {/* Table */}
            {report.columns && report.rows && (
              <DataTable
                columns={report.columns}
                rows={report.rows}
                totalsRow={report.totals_row}
              />
            )}

            {/* Pivot table (columns_list / rows_list) */}
            {report.columns_list && report.rows_list && (
              <DataTable
                columns={report.columns_list}
                rows={report.rows_list}
              />
            )}
          </div>
        ))}

        {reports.length === 0 && (
          <div className="text-center py-12 text-slate-600">
            <Lightbulb size={32} className="mx-auto mb-3 opacity-40" />
            <p className="text-sm">Run an analysis to see results here.</p>
          </div>
        )}
      </div>
    </div>
  )
}
