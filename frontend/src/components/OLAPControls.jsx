import { useState } from 'react'
import { ChevronDown, ChevronUp, Play, Loader2 } from 'lucide-react'
import axios from 'axios'

const DIMENSIONS = ['year', 'quarter', 'month', 'region', 'country', 'category', 'subcategory', 'customer_segment']
const MEASURES = ['revenue', 'profit', 'cost', 'quantity', 'profit_margin']
const HIERARCHIES = ['time', 'geography', 'product']
const HIERARCHY_LEVELS = {
  time: ['year', 'quarter', 'month'],
  geography: ['region', 'country'],
  product: ['category', 'subcategory'],
}

function Section({ title, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border border-white/10 rounded-xl overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-4 py-3 bg-white/5 hover:bg-white/10 transition-colors text-sm font-medium text-slate-200"
        onClick={() => setOpen(o => !o)}
      >
        {title}
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>
      {open && <div className="p-4 space-y-3">{children}</div>}
    </div>
  )
}

function Select({ label, value, onChange, options }) {
  return (
    <div>
      <p className="label">{label}</p>
      <select
        className="input w-full"
        value={value}
        onChange={e => onChange(e.target.value)}
      >
        {options.map(o => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </div>
  )
}

function RunBtn({ onClick, loading }) {
  return (
    <button className="btn-primary w-full flex items-center justify-center gap-2" onClick={onClick} disabled={loading}>
      {loading ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
      Run
    </button>
  )
}

export default function OLAPControls({ onResult, loading, setLoading }) {
  // Drill-down / Roll-up state
  const [drillHierarchy, setDrillHierarchy] = useState('time')
  const [drillFrom, setDrillFrom] = useState('year')
  const [drillDir, setDrillDir] = useState('down')

  // Slice state
  const [sliceDim, setSliceDim] = useState('year')
  const [sliceValue, setSliceValue] = useState('2024')
  const [sliceGroup, setSliceGroup] = useState('region')

  // Dice state
  const [diceYear, setDiceYear] = useState('2024')
  const [diceRegion, setDiceRegion] = useState('Europe')
  const [diceCategory, setDiceCategory] = useState('')

  // Pivot state
  const [pivotRows, setPivotRows] = useState('region')
  const [pivotCols, setPivotCols] = useState('year')
  const [pivotVals, setPivotVals] = useState('revenue')

  // KPI state
  const [yoyMeasure, setYoyMeasure] = useState('revenue')
  const [yoyGroup, setYoyGroup] = useState('region')
  const [topMeasure, setTopMeasure] = useState('revenue')
  const [topN, setTopN] = useState('5')
  const [topGroup, setTopGroup] = useState('country')
  const [marginGroup, setMarginGroup] = useState('category')

  const run = async (endpoint, body) => {
    setLoading(true)
    try {
      const { data } = await axios.post(endpoint, body)
      onResult({ results: [data.data], reports: [data.report], summary: data.summary || { text: '', highlights: [], recommendations: [] }, llm_used: false })
    } catch (err) {
      alert(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const runDrill = () => {
    const levels = HIERARCHY_LEVELS[drillHierarchy]
    const fromIdx = levels.indexOf(drillFrom)
    const toIdx = drillDir === 'down' ? fromIdx + 1 : fromIdx - 1
    if (toIdx < 0 || toIdx >= levels.length) return alert(`Cannot ${drillDir} from '${drillFrom}' in ${drillHierarchy} hierarchy.`)
    const endpoint = drillDir === 'down' ? '/api/olap/drill-down' : '/api/olap/roll-up'
    run(endpoint, { hierarchy: drillHierarchy, from_level: drillFrom })
  }

  return (
    <div className="h-full overflow-y-auto px-6 py-4 space-y-3">
      <h2 className="text-sm font-semibold text-slate-200 mb-1">Direct OLAP Operations</h2>

      {/* Drill-Down / Roll-Up */}
      <Section title="Dimension Navigation (Drill-Down / Roll-Up)" defaultOpen>
        <div className="grid grid-cols-2 gap-3">
          <Select label="Hierarchy" value={drillHierarchy} onChange={v => { setDrillHierarchy(v); setDrillFrom(HIERARCHY_LEVELS[v][0]) }} options={HIERARCHIES} />
          <Select label="From Level" value={drillFrom} onChange={setDrillFrom} options={HIERARCHY_LEVELS[drillHierarchy]} />
        </div>
        <div className="flex gap-2">
          <button
            className={`flex-1 text-sm py-2 rounded-lg border transition-colors ${drillDir === 'down' ? 'bg-brand-600 border-brand-500 text-white' : 'border-white/10 text-slate-400 hover:bg-white/5'}`}
            onClick={() => setDrillDir('down')}
          >↓ Drill Down</button>
          <button
            className={`flex-1 text-sm py-2 rounded-lg border transition-colors ${drillDir === 'up' ? 'bg-brand-600 border-brand-500 text-white' : 'border-white/10 text-slate-400 hover:bg-white/5'}`}
            onClick={() => setDrillDir('up')}
          >↑ Roll Up</button>
        </div>
        <RunBtn onClick={runDrill} loading={loading} />
      </Section>

      {/* Slice */}
      <Section title="Slice (single dimension filter)">
        <div className="grid grid-cols-2 gap-3">
          <Select label="Dimension" value={sliceDim} onChange={setSliceDim} options={DIMENSIONS} />
          <div>
            <p className="label">Value</p>
            <input className="input w-full" value={sliceValue} onChange={e => setSliceValue(e.target.value)} placeholder="e.g. 2024, Europe" />
          </div>
        </div>
        <Select label="Group By" value={sliceGroup} onChange={setSliceGroup} options={DIMENSIONS} />
        <RunBtn onClick={() => run('/api/olap/slice', { dimension: sliceDim, value: isNaN(sliceValue) ? sliceValue : Number(sliceValue), group_by: [sliceGroup], measures: ['revenue', 'profit'] })} loading={loading} />
      </Section>

      {/* Dice */}
      <Section title="Dice (multiple dimension filters)">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <p className="label">Year</p>
            <input className="input w-full" value={diceYear} onChange={e => setDiceYear(e.target.value)} placeholder="2024" />
          </div>
          <div>
            <p className="label">Region</p>
            <input className="input w-full" value={diceRegion} onChange={e => setDiceRegion(e.target.value)} placeholder="Europe" />
          </div>
          <div>
            <p className="label">Category</p>
            <input className="input w-full" value={diceCategory} onChange={e => setDiceCategory(e.target.value)} placeholder="optional" />
          </div>
        </div>
        <RunBtn onClick={() => {
          const filters = {}
          if (diceYear) filters.year = Number(diceYear)
          if (diceRegion) filters.region = diceRegion
          if (diceCategory) filters.category = diceCategory
          run('/api/olap/dice', { filters, measures: ['revenue', 'profit'] })
        }} loading={loading} />
      </Section>

      {/* Pivot */}
      <Section title="Pivot (cross-tabulation)">
        <div className="grid grid-cols-3 gap-3">
          <Select label="Rows" value={pivotRows} onChange={setPivotRows} options={DIMENSIONS} />
          <Select label="Columns" value={pivotCols} onChange={setPivotCols} options={DIMENSIONS} />
          <Select label="Values" value={pivotVals} onChange={setPivotVals} options={MEASURES} />
        </div>
        <RunBtn onClick={() => run('/api/olap/pivot', { rows: pivotRows, columns: pivotCols, values: pivotVals })} loading={loading} />
      </Section>

      {/* YoY Growth */}
      <Section title="KPI: Year-over-Year Growth">
        <div className="grid grid-cols-2 gap-3">
          <Select label="Measure" value={yoyMeasure} onChange={setYoyMeasure} options={MEASURES} />
          <Select label="Group By" value={yoyGroup} onChange={setYoyGroup} options={DIMENSIONS} />
        </div>
        <RunBtn onClick={() => run('/api/olap/kpi/yoy-growth', { measure: yoyMeasure, group_by: yoyGroup })} loading={loading} />
      </Section>

      {/* Top N */}
      <Section title="KPI: Top N Rankings">
        <div className="grid grid-cols-3 gap-3">
          <Select label="Measure" value={topMeasure} onChange={setTopMeasure} options={MEASURES} />
          <div>
            <p className="label">N</p>
            <input className="input w-full" type="number" value={topN} onChange={e => setTopN(e.target.value)} min={1} max={20} />
          </div>
          <Select label="Group By" value={topGroup} onChange={setTopGroup} options={DIMENSIONS} />
        </div>
        <RunBtn onClick={() => run('/api/olap/kpi/top-n', { measure: topMeasure, n: Number(topN), group_by: topGroup })} loading={loading} />
      </Section>

      {/* Profit Margins */}
      <Section title="KPI: Profit Margins">
        <Select label="Group By" value={marginGroup} onChange={setMarginGroup} options={DIMENSIONS} />
        <RunBtn onClick={() => run('/api/olap/kpi/margins', { group_by: marginGroup })} loading={loading} />
      </Section>
    </div>
  )
}
