import { useState } from 'react';
import { exportPDF, sendEmail } from '../services/api';

interface Props {
  results: any[];
  query: string;
  conversationId: string;
}

export function ExportToolbar({ results, query, conversationId }: Props) {
  const [email, setEmail] = useState('');
  const [showEmailInput, setShowEmailInput] = useState(false);
  const [status, setStatus] = useState('');

  const handlePDF = async () => {
    setStatus('Generating PDF...');
    try {
      const { download_url } = await exportPDF({
        results, query, conversation_id: conversationId, title: 'OLAP Analysis Report'
      });
      window.open(download_url, '_blank');
      setStatus('');
    } catch {
      setStatus('PDF generation failed');
    }
  };

  const handleEmail = async () => {
    if (!email.trim()) return;
    setStatus('Sending...');
    try {
      await sendEmail({
        to_email: email, subject: 'Your OLAP Analysis Report',
        results, query, conversation_id: conversationId
      });
      setStatus(`Sent to ${email}`);
      setShowEmailInput(false);
      setEmail('');
      setTimeout(() => setStatus(''), 3000);
    } catch {
      setStatus('Email send failed');
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-gray-100">
      <button onClick={handlePDF}
        className="flex items-center gap-1.5 px-3 py-1.5 bg-navy text-white
                   text-xs font-medium rounded hover:bg-navy-light transition-colors">
        Export PDF
      </button>
      <button onClick={() => setShowEmailInput(!showEmailInput)}
        className="flex items-center gap-1.5 px-3 py-1.5 bg-green-700 text-white
                   text-xs font-medium rounded hover:bg-green-800 transition-colors">
        Email Report
      </button>
      {showEmailInput && (
        <div className="flex gap-2 items-center">
          <input
            type="email" value={email} onChange={e => setEmail(e.target.value)}
            placeholder="recipient@email.com"
            className="border border-gray-300 rounded px-2.5 py-1.5 text-xs w-48
                       focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <button onClick={handleEmail}
            className="px-3 py-1.5 bg-green-600 text-white text-xs rounded hover:bg-green-700">
            Send
          </button>
        </div>
      )}
      {status && (
        <span className="text-xs text-gray-500 italic">{status}</span>
      )}
    </div>
  );
}
