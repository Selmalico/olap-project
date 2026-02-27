import { useState } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";
import clsx from "clsx";

function cellColor(val) {
  if (val == null) return "";
  const s = String(val);
  if (s.startsWith("+") || (s.includes("%") && parseFloat(s) > 0))
    return "text-emerald-600";
  if (s.startsWith("-") || (s.includes("%") && parseFloat(s) < 0))
    return "text-rose-600";
  return "";
}

function formatCell(val) {
  if (val == null) return "—";
  if (typeof val === "number") {
    if (Number.isInteger(val)) return val.toLocaleString();
    return val.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
  return String(val);
}

export default function DataTable({
  columns,
  rows,
  totalsRow,
  data,
  report,
  light,
}) {
  const [sortCol, setSortCol] = useState(null);
  const [sortDir, setSortDir] = useState("asc");

  let cols = columns;
  let rws = rows;
  let totals = totalsRow;
  if (report) {
    cols = report.columns_list?.length ? report.columns_list : report.columns;
    rws = report.rows_list?.length ? report.rows_list : report.rows;
    totals = report.totals_row;
  } else if (data && Array.isArray(data)) {
    rws = data;
    cols = data[0] ? Object.keys(data[0]) : [];
  } else if (data && data.rows && data.columns) {
    rws = data.rows;
    cols = data.columns;
    totals = data.totals_row;
  }

  if (!rws || rws.length === 0)
    return <p className="text-slate-500 text-sm py-4">No data.</p>;

  const handleSort = (col) => {
    if (sortCol === col) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortCol(col);
      setSortDir("asc");
    }
  };

  const sorted = [...rws].sort((a, b) => {
    if (!sortCol) return 0;
    const av = a[sortCol],
      bv = b[sortCol];
    if (av == null) return 1;
    if (bv == null) return -1;
    const cmp =
      typeof av === "number" && typeof bv === "number"
        ? av - bv
        : String(av).localeCompare(String(bv));
    return sortDir === "asc" ? cmp : -cmp;
  });

  // Force dark theme
  const isLight = false;
  const thCls = "bg-slate-800 text-slate-300 hover:bg-slate-700";
  const trCls = "border-b border-slate-700 hover:bg-slate-800/50";
  const tdCls = "text-slate-200";
  const totalsCls = "bg-slate-800 border-slate-600 font-medium text-slate-100";

  return (
    <div
      className={clsx(
        "overflow-x-auto rounded-xl border shadow-sm",
        "border-slate-700 bg-slate-900",
      )}
    >
      <table className="w-full text-xs">
        <thead>
          <tr className={clsx("border-b", "border-slate-700")}>
            {cols.map((col) => (
              <th
                key={col}
                className={clsx(
                  "px-3 py-2.5 text-left font-semibold uppercase tracking-wider cursor-pointer select-none whitespace-nowrap transition-colors",
                  thCls,
                )}
                onClick={() => handleSort(col)}
              >
                <span className="flex items-center gap-1">
                  {String(col).replace(/_/g, " ")}
                  {sortCol === col ? (
                    sortDir === "asc" ? (
                      <ChevronUp size={10} />
                    ) : (
                      <ChevronDown size={10} />
                    )
                  ) : null}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr
              key={i}
              className={clsx(
                "transition-colors",
                trCls,
                i % 2 === 0 ? "" : "bg-slate-800/30",
              )}
            >
              {cols.map((col) => (
                <td
                  key={col}
                  className={clsx(
                    "px-3 py-2 whitespace-nowrap",
                    tdCls,
                    cellColor(row[col]),
                  )}
                >
                  {formatCell(row[col])}
                </td>
              ))}
            </tr>
          ))}
          {totals && (
            <tr className={clsx("border-t-2", totalsCls)}>
              {cols.map((col) => (
                <td key={col} className="px-3 py-2.5 whitespace-nowrap">
                  {totals[col] != null && col !== "_totals"
                    ? formatCell(totals[col])
                    : col === cols[0]
                      ? "Total"
                      : ""}
                </td>
              ))}
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
