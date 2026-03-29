"use client";
import useWebSocket from "react-use-websocket";
import { useState, useCallback, useEffect } from "react";
import { Bell, TrendingUp, Zap, Activity } from "lucide-react";
import { API_BASE } from "@/lib/api";

interface Alert {
  id: string;
  ticker?: string;
  type: string;
  score?: number;
  recommendation?: string;
  timestamp: string;
}

const SIGNAL_COLORS: Record<string, string> = {
  ET_OPPORTUNITY: "indigo",
  BULK_BLOCK: "amber",
  FII_DII_FLOW: "emerald",
  NSE_PATTERN: "violet",
  PIPELINE_SCAN: "blue",
  SYSTEM_READY: "emerald",
  SCAN_ERROR: "red",
};

function colorClass(type: string) {
  const c = SIGNAL_COLORS[type] || "indigo";
  const classMap: Record<string, string> = {
    indigo: "bg-indigo-500/20 text-indigo-400 border border-indigo-500/20",
    amber: "bg-amber-500/20 text-amber-400 border border-amber-500/20",
    emerald: "bg-emerald-500/20 text-emerald-400 border border-emerald-500/20",
    violet: "bg-violet-500/20 text-violet-400 border border-violet-500/20",
    blue: "bg-blue-500/20 text-blue-400 border border-blue-500/20",
    red: "bg-red-500/20 text-red-400 border border-red-500/20",
  };
  return classMap[c] || classMap.indigo;
}

export default function AlertPanel() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [connected, setConnected] = useState(false);

  // Pre-seed with live radar signals immediately — panel is never blank
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/radar/opportunities`)
      .then((r) => r.json())
      .then((j) => {
        const sigs = (j.signals || []).slice(0, 8);
        const seeded: Alert[] = sigs.map((s: {
          id?: string; signal_type?: string; ticker?: string;
          confidence?: number; description?: string; timestamp?: string;
        }) => ({
          id: s.id || String(Math.random()),
          type: s.signal_type || "ET_OPPORTUNITY",
          ticker: s.ticker || "MARKET",
          score: Math.round((s.confidence || 0.5) * 10),
          recommendation: (s.description || "").slice(0, 220),
          timestamp: s.timestamp
            ? new Date(s.timestamp).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })
            : "live",
        }));
        setAlerts(seeded);
      })
      .catch(() => {});
  }, []);

  const onMessage = useCallback((event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data as string);
      if (data && data.type) {
        setAlerts((prev) =>
          [
            {
              id: String(data.timestamp || Math.random()),
              type: data.type,
              ticker: data.ticker,
              score: data.score,
              recommendation: data.recommendation,
              timestamp: data.timestamp ||
                new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
            },
            ...prev,
          ].slice(0, 50)
        );
      }
    } catch (e) {
      console.error(e);
    }
  }, []);

  // Fixed URL — must have trailing slash to match FastAPI route /ws/alerts/
  useWebSocket("ws://localhost:8000/ws/alerts/", {
    shouldReconnect: () => true,
    reconnectAttempts: 20,
    reconnectInterval: 3000,
    onMessage,
    onOpen: () => setConnected(true),
    onClose: () => setConnected(false),
  });

  return (
    <div className="bg-slate-900/80 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50 shadow-2xl h-full overflow-hidden flex flex-col relative group">
      <div className="absolute -top-24 -right-24 w-48 h-48 bg-indigo-500/20 rounded-full blur-3xl group-hover:bg-indigo-500/30 transition-all duration-700"></div>

      <div className="flex items-center justify-between mb-4 z-10">
        <h2 className="text-xl font-bold text-white flex items-center tracking-tight">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center mr-3 border border-indigo-500/30">
            <Bell className="w-4 h-4 text-indigo-400" />
          </div>
          Live Intelligence
        </h2>
        <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-full border shadow-lg transition-all ${
          connected ? "bg-emerald-500/10 border-emerald-500/20" : "bg-amber-500/10 border-amber-500/20"
        }`}>
          <span className="relative flex h-2 w-2">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${connected ? "bg-emerald-400" : "bg-amber-400"}`}></span>
            <span className={`relative inline-flex rounded-full h-2 w-2 ${connected ? "bg-emerald-500" : "bg-amber-500"}`}></span>
          </span>
          <span className={`text-xs font-semibold ${connected ? "text-emerald-400" : "text-amber-400"}`}>
            {connected ? "Live WS" : "REST feed"}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar z-10">
        {alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 opacity-60">
            <Activity className="w-12 h-12 mb-4 animate-[pulse_3s_ease-in-out_infinite] text-indigo-400/50" />
            <p className="text-sm font-medium">Loading market intelligence...</p>
          </div>
        ) : (
          alerts.map((alert, i) => (
            <div
              key={i}
              className="group/item relative p-4 rounded-xl bg-gradient-to-br from-slate-800 to-slate-800/50 border border-slate-700/50 hover:border-indigo-500/40 transition-all duration-300 hover:shadow-lg hover:shadow-indigo-500/10"
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${colorClass(alert.type)}`}>
                    {alert.type.replace(/_/g, " ")}
                  </span>
                  {alert.ticker && alert.ticker !== "MARKET" && (
                    <span className="text-[10px] font-bold text-slate-300 bg-slate-700/60 px-2 py-0.5 rounded">
                      {alert.ticker}
                    </span>
                  )}
                </div>
                <span className="text-[10px] font-medium text-slate-500 flex-shrink-0 ml-1">
                  {alert.timestamp}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed mb-3">
                {alert.recommendation || "Signal detected."}
              </p>

              <div className="flex items-center justify-between pt-2 border-t border-slate-700/50">
                <div className="flex items-center space-x-1.5 text-amber-400 bg-amber-500/10 px-2 py-1 rounded border border-amber-500/20">
                  <Zap className="w-3 h-3" />
                  <span className="text-[10px] font-semibold">
                    Conviction <span className="text-white ml-0.5">{(alert.score || 8.5).toFixed(1)}/10</span>
                  </span>
                </div>
                <button className="text-[10px] font-semibold text-indigo-400 hover:text-indigo-300 transition-colors flex items-center bg-indigo-500/10 hover:bg-indigo-500/20 px-2.5 py-1 rounded border border-indigo-500/20">
                  Analyze <TrendingUp className="w-3 h-3 ml-1" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
