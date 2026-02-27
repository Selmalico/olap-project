import { useState } from 'react';
import { useChat } from '../hooks/useChat';
import { AgentTracker } from '../components/AgentTracker';
import { DataTable } from '../components/DataTable';
import { ReportChart } from '../components/ReportChart';
import { ChartPanel } from '../components/ChartPanel';
import { ExportToolbar } from '../components/ExportToolbar';
import { MessageSquare, Sparkles, Loader2, AlertCircle, Lightbulb, TrendingUp, BarChart2 } from 'lucide-react';

const STARTER_QUESTIONS = [
  'Compare 2023 vs 2024 revenue by region',
  'Show top 5 countries by profit margin',
  'Show YoY growth by category',
  'Show month-over-month revenue trend for 2024',
  'How many transactions were made in Q4 2023?',
  'What is the total revenue in 2024?',
  'How many orders were placed in Europe in 2023?',
  'What is the average profit margin by category?',
  'Drill down from year to quarter',
  'Roll up from month to year level',
  'Pivot revenue by region and year',
  'What is the revenue share by region?',
  'Slice data for Electronics in 2024',
  'Dice: Electronics in Europe 2024',
  'Drill through to raw transactions for 2024',
  'Show YTD cumulative revenue for 2024',
  'Show 3-month rolling average for revenue',
  'Which customer segment is most profitable?',
];

export default function Chat() {
  const { messages, loading, conversationId, sendMessage, clearChat } = useChat();
  const [input, setInput] = useState('');

  const handleSubmit = () => {
    if (!input.trim() || loading) return;
    sendMessage(input.trim());
    setInput('');
  };

  return (
    <div className="flex flex-col h-screen max-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      {/* Header */}
      <header className="shrink-0 flex items-center justify-between px-6 py-4 bg-white/90 backdrop-blur border-b border-slate-200/80 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-[#1E3A5F] to-[#2E75B6] text-white shadow-md">
            <BarChart2 className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-800">OLAP BI Assistant</h1>
            <p className="text-xs text-slate-500">Multi-agent analytics · Slice, Dice, Drill-Down/Up/Through, Pivot, YoY, MoM, YTD, Rolling Avg</p>
          </div>
        </div>
        <button
          onClick={clearChat}
          className="text-xs text-slate-500 hover:text-slate-700 px-3 py-1.5 rounded-lg hover:bg-slate-100 transition-colors font-medium"
        >
          Clear chat
        </button>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto px-4 sm:px-6 py-5 max-w-4xl mx-auto w-full space-y-6">
        {messages.length === 0 && (
          <div className="text-center pt-16 pb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-slate-100 text-slate-400 mb-6">
              <MessageSquare className="w-8 h-8" />
            </div>
            <p className="text-slate-600 font-medium mb-1">Ask a business question</p>
            <p className="text-slate-500 text-sm mb-8 max-w-sm mx-auto">
              Use natural language or try one of the suggested queries below.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {STARTER_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="px-4 py-2.5 bg-white border border-slate-200 text-slate-700 text-sm rounded-xl hover:border-[#2E75B6] hover:bg-[#2E75B6]/5 hover:text-[#1E3A5F] transition-all shadow-sm"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-full ${msg.role === 'user' ? 'max-w-xl' : 'w-full'}`}>
              {msg.role === 'user' ? (
                <div className="bg-gradient-to-br from-[#1E3A5F] to-[#2E75B6] text-white px-4 py-3 rounded-2xl rounded-br-md shadow-md">
                  <p className="text-sm leading-relaxed">{msg.content}</p>
                </div>
              ) : (
                <div className="bg-white border border-slate-200/80 rounded-2xl rounded-tl-md p-5 shadow-lg shadow-slate-200/50 space-y-4">
                  {/* Agents & actions */}
                  {(msg.operations?.length || msg.agentsUsed?.length) && (
                    <AgentTracker
                      operations={msg.operations}
                      agents={msg.agentsUsed}
                      loading={false}
                    />
                  )}

                  {/* Summary */}
                  <div className="space-y-2">
                    <p className="text-sm text-slate-700 leading-relaxed">{msg.content}</p>
                    {msg.summary?.highlights?.length > 0 && (
                      <ul className="space-y-1 pl-4 border-l-2 border-emerald-200">
                        {msg.summary.highlights.map((h, i) => (
                          <li key={i} className="text-xs text-emerald-800 flex items-start gap-2">
                            <TrendingUp className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                            {h}
                          </li>
                        ))}
                      </ul>
                    )}
                    {msg.summary?.recommendations?.length > 0 && (
                      <div className="flex flex-wrap gap-2 pt-2">
                        {msg.summary.recommendations.map((r, i) => (
                          <div
                            key={i}
                            className="inline-flex items-start gap-1.5 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-2.5 py-1.5"
                          >
                            <Lightbulb className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                            {r}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Results: reports (tables + charts) */}
                  {msg.reports?.length > 0 && (
                    <div className="space-y-6 pt-2 border-t border-slate-100">
                      {msg.reports.map((report, i) => (
                        <section key={i} className="space-y-3">
                          <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                            <Sparkles className="w-4 h-4 text-amber-500" />
                            {report.title}
                          </h3>
                          <ReportChart report={report} height={220} className="rounded-xl border border-slate-200 bg-slate-50/50 p-3" />
                          <DataTable report={report} light />
                        </section>
                      ))}
                    </div>
                  )}

                  {/* Fallback: raw result data (e.g. from orchestrator) */}
                  {!msg.reports?.length && msg.results?.length > 0 && (
                    <div className="space-y-6 pt-2 border-t border-slate-100">
                      {msg.results.map((result: any, i: number) => {
                        const rows = result.rows_list ?? result.rows;
                        const cols = result.columns_list ?? result.columns;
                        if (!rows?.length) return null;
                        const opLabel = (result.operation || result._tool || '').replace(/_/g, ' ');
                        return (
                          <section key={i} className="space-y-3">
                            {opLabel && (
                              <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                                <Sparkles className="w-4 h-4 text-amber-500" />
                                {opLabel.replace(/\b\w/g, (c: string) => c.toUpperCase())}
                              </h3>
                            )}
                            {result.chart_config && (
                              <ChartPanel data={rows} config={result.chart_config} />
                            )}
                            <DataTable columns={cols} rows={rows} totalsRow={result.totals_row} light />
                            {result.anomalies?.length > 0 && (
                              <div className="space-y-1.5">
                                {result.anomalies.map((a: string, j: number) => (
                                  <div
                                    key={j}
                                    className="flex items-start gap-2 text-xs bg-amber-50 border-l-2 border-amber-400 px-3 py-2 text-amber-900 rounded-r-lg"
                                  >
                                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                                    {a}
                                  </div>
                                ))}
                              </div>
                            )}
                          </section>
                        );
                      })}
                    </div>
                  )}

                  {msg.error && (
                    <div className="flex items-start gap-2 text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">
                      <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                      {msg.content}
                    </div>
                  )}

                  {msg.results?.length > 0 && conversationId && (
                    <ExportToolbar
                      results={msg.results}
                      query={msg.content}
                      conversationId={conversationId}
                    />
                  )}

                  {msg.followUps?.length > 0 && (
                    <div className="pt-3 border-t border-slate-100">
                      <p className="text-xs text-slate-500 font-medium mb-2">Suggested follow-ups</p>
                      <div className="flex flex-wrap gap-2">
                        {msg.followUps.map((q, i) => (
                          <button
                            key={i}
                            onClick={() => sendMessage(q)}
                            className="text-xs px-3 py-1.5 bg-slate-100 text-slate-600 rounded-lg hover:bg-[#2E75B6]/10 hover:text-[#1E3A5F] transition-colors"
                          >
                            {q}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-md p-4 shadow-lg max-w-md w-full">
              <AgentTracker loading operations={[]} />
              <div className="flex items-center gap-2 mt-3 text-slate-500 text-sm">
                <Loader2 className="w-4 h-4 animate-spin shrink-0" />
                <span>Running OLAP pipeline…</span>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Input */}
      <div className="shrink-0 px-4 sm:px-6 py-4 bg-white/80 backdrop-blur border-t border-slate-200/80">
        <div className="flex gap-3 max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSubmit()}
            placeholder="Ask a business question… e.g. Compare Q3 vs Q4 2024 by region"
            disabled={loading}
            className="flex-1 border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#2E75B6]/40 focus:border-[#2E75B6] disabled:bg-slate-50 disabled:cursor-not-allowed shadow-inner"
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !input.trim()}
            className="px-5 py-3 bg-gradient-to-r from-[#1E3A5F] to-[#2E75B6] text-white font-semibold text-sm rounded-xl shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            {loading ? 'Analyzing…' : 'Analyze'}
          </button>
        </div>
      </div>
    </div>
  );
}
