import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const api = axios.create({ baseURL: API_BASE });

export const queryOLAP = (query: string, history: any[], conversationId?: string) =>
  api.post('/query', { query, history, conversation_id: conversationId }).then(r => r.data);

export const exportPDF = (data: any) =>
  api.post('/export/pdf', data).then(r => r.data);

export const sendEmail = (data: any) =>
  api.post('/email/send', data).then(r => r.data);

export const getSchema = () =>
  api.get('/schema').then(r => r.data);

export default api;
