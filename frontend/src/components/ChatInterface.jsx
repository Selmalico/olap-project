import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Sparkles, Loader2 } from 'lucide-react'
import axios from 'axios'

const SUGGESTIONS = [
  'What is total revenue by region for 2024?',
  'Show YoY growth by category',
  'Top 5 countries by profit',
  'Drill down from year to quarter',
  'Compare Q3 vs Q4 2024 revenue',
  'Show profit margin by category',
  'Monthly revenue trend for 2024',
  'Revenue share by region',
]

export default function ChatInterface({ onResult, loading, setLoading }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hello! I'm your AI BI analyst. Ask me anything about the Global Retail Sales data — I'll route your question through our specialist agents.",
    },
  ])
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (query) => {
    const q = (query || input).trim()
    if (!q || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: q }])
    setLoading(true)

    try {
      const { data } = await axios.post('/api/query/', { query: q })
      onResult(data)

      const llmNote = data.llm_used ? '' : (data.llm_fallback_reason ? ` *(${data.llm_fallback_reason})*` : ' *(keyword routing — add OPENAI_API_KEY in backend/.env for full AI)*')
      const summaryText = data.summary?.text || 'Analysis complete.'
      const highlights = data.summary?.highlights || []

      let responseText = summaryText + llmNote
      if (highlights.length) {
        responseText += '\n\n**Key findings:**\n' + highlights.map(h => `• ${h}`).join('\n')
      }
      const recs = data.summary?.recommendations || []
      if (recs.length) {
        responseText += '\n\n**Recommendations:**\n' + recs.map(r => `• ${r}`).join('\n')
      }

      setMessages(prev => [...prev, { role: 'assistant', content: responseText }])
    } catch (err) {
      const data = err.response?.data
      let msg = data?.error || data?.detail || err.message
      if (data?.traceback) msg += '\n\n' + data.traceback
      if (!msg) msg = 'Is the backend running?'
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: `Error: ${msg}` },
      ])
      if (data && !err.response?.data?.error) onResult(data)
    } finally {
      setLoading(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
              msg.role === 'user' ? 'bg-brand-600' : 'bg-slate-700'
            }`}>
              {msg.role === 'user' ? <User size={13} /> : <Bot size={13} />}
            </div>
            <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
              msg.role === 'user'
                ? 'bg-brand-600 text-white rounded-tr-sm'
                : 'bg-white/5 border border-white/10 text-slate-200 rounded-tl-sm'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-lg bg-slate-700 flex items-center justify-center shrink-0">
              <Bot size={13} />
            </div>
            <div className="bg-white/5 border border-white/10 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2 text-slate-400 text-sm">
              <Loader2 size={14} className="animate-spin" />
              Routing through agents…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div className="px-6 pb-2 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              onClick={() => send(s)}
              className="flex items-center gap-1.5 text-xs bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg px-3 py-1.5 text-slate-400 hover:text-white transition-colors"
            >
              <Sparkles size={10} />
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="px-6 py-4 border-t border-white/10">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            className="input flex-1"
            placeholder="Ask a business intelligence question…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={loading}
          />
          <button
            className="btn-primary px-3 py-2.5"
            onClick={() => send()}
            disabled={loading || !input.trim()}
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </div>
      </div>
    </div>
  )
}
