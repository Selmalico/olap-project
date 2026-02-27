import { useState, useCallback } from 'react';
import { queryOLAP } from '../services/api';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  results?: any[];
  reports?: any[];
  summary?: { text?: string; highlights?: string[]; recommendations?: string[] };
  operations?: string[];
  agentsUsed?: string[];
  followUps?: string[];
  llmUsed?: boolean;
  error?: string;
  timestamp: Date;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeAgents, setActiveAgents] = useState<string[]>([]);
  const [lastResults, setLastResults] = useState<any>(null);
  const [conversationId, setConversationId] = useState<string | undefined>();

  const sendMessage = useCallback(async (query: string) => {
    setLoading(true);
    setActiveAgents([]);
    const history = messages.map(m => ({ role: m.role, content: m.content }));
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      const response = await queryOLAP(query, history, conversationId);
      setConversationId(response.conversation_id);
      const operations = (response.results || [])
        .map((r: any) => r.operation || r._tool)
        .filter(Boolean)
        .filter((op: string, idx: number, arr: string[]) => arr.indexOf(op) === idx); // deduplicate
      setActiveAgents(response.agents_used || operations);
      setLastResults(response);

      const summary = response.summary || {};
      // Build a meaningful content string from available data
      let contentText = summary.text || '';
      if (!contentText && response.executive_summary) {
        contentText = response.executive_summary;
      }
      if (!contentText) {
        // Generate a summary from results
        const resultCount = (response.results || []).filter((r: any) => !r.error && r.rows?.length).length;
        const agentList = (response.agents_used || operations).join(', ');
        contentText = resultCount > 0
          ? `Analysis complete — ${resultCount} result set(s) returned using: ${agentList || 'multi-agent pipeline'}.`
          : 'Query processed. See the results below.';
      }

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: contentText,
        results: response.results,
        reports: response.reports,
        summary: {
          text: summary.text,
          highlights: summary.highlights || [],
          recommendations: summary.recommendations || [],
        },
        operations,
        agentsUsed: response.agents_used || operations,
        followUps: response.follow_up_questions || [],
        llmUsed: response.llm_used,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (e: any) {
      const detail = e.response?.data?.detail;
      const errMsg =
        typeof detail === 'string'
          ? detail
          : detail?.message || detail?.error || e.message || 'Something went wrong';
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Error: ${errMsg}`,
          error: errMsg,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [messages, conversationId]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setConversationId(undefined);
    setLastResults(null);
  }, []);

  return { messages, loading, activeAgents, lastResults, conversationId, sendMessage, clearChat };
}
