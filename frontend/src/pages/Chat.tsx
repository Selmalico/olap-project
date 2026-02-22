import { useState } from 'react';
import { useChat } from '../hooks/useChat';
import { AgentTracker } from '../components/AgentTracker';
import { DataTable } from '../components/DataTable';
import { ChartPanel } from '../components/ChartPanel';
import { ExportToolbar } from '../components/ExportToolbar';

const STARTER_QUESTIONS = [
  "Compare 2023 vs 2024 revenue by region",
  "Show top 5 countries by profit margin",
  "Drill down Q4 2024 by month for Electronics",
  "What are the most profitable product categories?",
  "Detect any unusual patterns in 2024 sales data"
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
    <div className="flex flex-col h-screen max-h-screen bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 bg-white border-b border-gray-200 shadow-sm">
        <div>
          <h1 className="text-lg font-bold text-navy">OLAP BI Assistant</h1>
          <p className="text-xs text-gray-500">7-agent AI platform &middot; DuckDB on S3</p>
        </div>
        <button onClick={clearChat} className="text-xs text-gray-400 hover:text-gray-600">
          Clear chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center pt-12">
            <p className="text-gray-500 text-sm mb-6">Start by asking a business question</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {STARTER_QUESTIONS.map(q => (
                <button key={q} onClick={() => sendMessage(q)}
                  className="px-3 py-2 bg-white border border-blue-200 text-blue-700 text-xs
                             rounded-full hover:bg-blue-50 hover:border-blue-400 transition-colors">
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-4xl w-full ${msg.role === 'user' ? 'max-w-xl' : ''}`}>
              {msg.role === 'user' ? (
                <div className="bg-navy text-white px-4 py-2.5 rounded-2xl rounded-br-sm text-sm ml-auto inline-block float-right">
                  {msg.content}
                </div>
              ) : (
                <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm p-4 shadow-sm">
                  {/* Agent tracker */}
                  {msg.agentsUsed && msg.agentsUsed.length > 0 && (
                    <AgentTracker agents={msg.agentsUsed} loading={false} />
                  )}
                  {/* Executive summary */}
                  <p className="text-sm text-gray-800 mt-2 leading-relaxed">{msg.content}</p>
                  {/* Results */}
                  {msg.results?.map((result: any, i: number) => {
                    if (!result.data && !result.chart_config) return null;
                    const chartResult = msg.results?.find((r: any) => r.agent_name === 'visualization_agent');
                    return (
                      <div key={i}>
                        {result.data && result.data.length > 0 && i === 0 && (
                          <>
                            <DataTable data={result.data} />
                            {chartResult?.chart_config && (
                              <ChartPanel data={result.data} config={chartResult.chart_config} />
                            )}
                          </>
                        )}
                        {result.anomalies && result.anomalies.length > 0 && (
                          <div className="mt-3 space-y-1">
                            {result.anomalies.map((a: string, j: number) => (
                              <div key={j} className="text-xs bg-amber-50 border-l-2 border-amber-400 px-3 py-1.5 text-amber-800">
                                {a}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {/* Export toolbar */}
                  {msg.results && conversationId && (
                    <ExportToolbar results={msg.results} query={msg.content}
                      conversationId={conversationId} />
                  )}
                  {/* Follow-up questions */}
                  {msg.followUps && msg.followUps.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <p className="text-xs text-gray-400 mb-2">Follow-up questions:</p>
                      <div className="flex flex-wrap gap-2">
                        {msg.followUps.map((q: string, i: number) => (
                          <button key={i} onClick={() => sendMessage(q)}
                            className="text-xs px-2.5 py-1 bg-blue-50 text-blue-600
                                       border border-blue-200 rounded-full hover:bg-blue-100">
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
            <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm p-4 shadow-sm max-w-xl">
              <AgentTracker agents={[]} loading={true} />
            </div>
          </div>
        )}
      </div>

      {/* Input bar */}
      <div className="px-6 py-4 bg-white border-t border-gray-200">
        <div className="flex gap-3 max-w-4xl mx-auto">
          <input
            type="text" value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            placeholder="Ask a business question... e.g. 'Compare Q3 vs Q4 2024 by region'"
            disabled={loading}
            className="flex-1 border border-gray-300 rounded-xl px-4 py-2.5 text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-400
                       disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button onClick={handleSubmit} disabled={loading || !input.trim()}
            className="px-5 py-2.5 bg-navy text-white font-medium text-sm rounded-xl
                       hover:bg-navy-light disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors">
            {loading ? '...' : 'Analyze'}
          </button>
        </div>
      </div>
    </div>
  );
}
