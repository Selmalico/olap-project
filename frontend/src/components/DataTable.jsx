import { useState } from 'react'
import { ChevronUp, ChevronDown } from 'lucide-react'
import clsx from 'clsx'

function cellColor(val) {
  if (typeof val !== 'string') return ''
  if (val.startsWith('+')) return 'text-emerald-400'
  if (val.startsWith('-')) return 'text-red-400'
  return ''
}

export default function DataTable({ columns, rows, totalsRow }) {
  const [sortCol, setSortCol] = useState(null)
  const [sortDir, setSortDir] = useState('asc')

  if (!rows || rows.length === 0) return <p className="text-slate-500 text-sm">No data.</p>

  const handleSort = (col) => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortCol(col); setSortDir('asc') }
  }

  const sorted = [...rows].sort((a, b) => {
    if (!sortCol) return 0
    const av = a[sortCol], bv = b[sortCol]
    if (av == null) return 1
    if (bv == null) return -1
    const cmp = typeof av === 'number' && typeof bv === 'number'
      ? av - bv
      : String(av).localeCompare(String(bv))
    return sortDir === 'asc' ? cmp : -cmp
  })

  return (
    <div className="overflow-x-auto rounded-xl border border-white/10">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-white/5 border-b border-white/10">
            {columns.map(col => (
              <th
                key={col}
                className="px-3 py-2.5 text-left font-medium text-slate-400 uppercase tracking-wide cursor-pointer hover:text-white select-none whitespace-nowrap"
                onClick={() => handleSort(col)}
              >
                <span className="flex items-center gap-1">
                  {col.replace(/_/g, ' ')}
                  {sortCol === col
                    ? sortDir === 'asc' ? <ChevronUp size={10} /> : <ChevronDown size={10} />
                    : null}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr key={i} className={clsx('border-b border-white/5 hover:bg-white/5 transition-colors', i % 2 === 0 ? '' : 'bg-white/[0.02]')}>
              {columns.map(col => (
                <td key={col} className={clsx('px-3 py-2 text-slate-200 whitespace-nowrap', cellColor(String(row[col] ?? '')))}>
                  {row[col] == null ? <span className="text-slate-600">—</span> : String(row[col])}
                </td>
              ))}
            </tr>
          ))}
          {totalsRow && (
            <tr className="bg-white/5 border-t border-white/20 font-medium">
              {columns.map(col => (
                <td key={col} className="px-3 py-2.5 text-slate-200 whitespace-nowrap">
                  {totalsRow[col] != null && col !== '_totals' ? String(totalsRow[col]) : ''}
                </td>
              ))}
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
