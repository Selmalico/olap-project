import { useState } from 'react';

interface Props {
  data: any[];
  maxRows?: number;
}

export function DataTable({ data, maxRows = 20 }: Props) {
  const [showAll, setShowAll] = useState(false);
  if (!data || data.length === 0) return null;

  const cols = Object.keys(data[0]);
  const rows = showAll ? data : data.slice(0, maxRows);

  const formatVal = (val: any) => {
    if (val === null || val === undefined) return '\u2014';
    if (typeof val === 'number') {
      return val > 1000
        ? val.toLocaleString('en-US', { maximumFractionDigits: 2 })
        : val.toFixed(2);
    }
    return String(val);
  };

  return (
    <div className="overflow-x-auto rounded border border-gray-200 mt-3">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="bg-navy text-white">
            {cols.map(c => (
              <th key={c} className="px-4 py-2.5 text-left font-medium whitespace-nowrap">
                {c.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-blue-50'}>
              {cols.map(c => (
                <td key={c} className="px-4 py-2 text-gray-700 whitespace-nowrap">
                  {formatVal(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length > maxRows && !showAll && (
        <button onClick={() => setShowAll(true)}
          className="w-full py-2 text-sm text-blue-600 hover:bg-blue-50 border-t border-gray-200">
          Show all {data.length} rows
        </button>
      )}
    </div>
  );
}
