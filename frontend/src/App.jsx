import { useState, useEffect } from "react";
import { BarChart3, MessageSquare, Layers, TrendingUp } from "lucide-react";
import ChatInterface from "./components/ChatInterface";
import OLAPControls from "./components/OLAPControls";
import KPICard from "./components/KPICard";
import ResultsPanel from "./components/ResultsPanel";
import axios from "axios";

const TABS = [
  { id: "chat", label: "Ask AI", icon: MessageSquare },
  { id: "olap", label: "OLAP Controls", icon: Layers },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("chat");
  const [kpiCards, setKpiCards] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    axios
      .get("/api/query/dashboard")
      .then((r) => setKpiCards(r.data.cards || []))
      .catch(() => {});
  }, []);

  return (
    <div className="flex flex-col h-full">
      {/* Top bar */}
      <header className="flex items-center gap-3 px-6 py-4 border-b border-white/10 bg-slate-950/80 backdrop-blur shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
            <BarChart3 size={16} className="text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white leading-none">
              OLAP Analytics
            </h1>
            <p className="text-xs text-slate-500 leading-none mt-0.5">
              Business Intelligence Platform
            </p>
          </div>
        </div>

        <div className="ml-auto flex items-center gap-2 text-xs text-slate-500">
          <TrendingUp size={12} />
          <span>Global Retail Sales · 2022–2024</span>
        </div>
      </header>

      {/* KPI bar */}
      {kpiCards.length > 0 && (
        <div className="flex gap-3 px-6 py-3 overflow-x-auto border-b border-white/5 shrink-0 bg-slate-950/50">
          {kpiCards.map((card, i) => (
            <KPICard key={i} {...card} />
          ))}
        </div>
      )}

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <nav className="w-48 shrink-0 border-r border-white/10 p-3 flex flex-col gap-1">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors text-left ${
                  activeTab === tab.id
                    ? "bg-brand-600 text-white"
                    : "text-slate-400 hover:bg-white/5 hover:text-white"
                }`}
              >
                <Icon size={15} />
                {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Main content */}
        <main className="flex-1 flex overflow-hidden">
          <div className="flex-1 overflow-hidden">
            {activeTab === "chat" ? (
              <ChatInterface
                onResult={setResult}
                loading={loading}
                setLoading={setLoading}
              />
            ) : (
              <OLAPControls
                onResult={setResult}
                loading={loading}
                setLoading={setLoading}
              />
            )}
          </div>

          {/* Results panel */}
          {result && (
            <div className="w-[520px] shrink-0 border-l border-white/10 overflow-y-auto">
              <ResultsPanel result={result} onClose={() => setResult(null)} />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
