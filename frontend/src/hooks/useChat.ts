import { useState, useCallback } from 'react';
import { queryOLAP } from '../services/api';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  results?: any[];
  agentsUsed?: string[];
  followUps?: string[];
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
      setActiveAgents(response.agents_used || []);
      setLastResults(response);

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.executive_summary || 'Analysis complete. See results below.',
        results: response.results,
        agentsUsed: response.agents_used,
        followUps: response.follow_up_questions,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (e: any) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${e.response?.data?.detail || e.message || 'Something went wrong'}`,
        timestamp: new Date()
      }]);
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
