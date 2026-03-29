"use client";
import { useEffect, useState, startTransition } from "react";
import { Target, Activity, AlertCircle, ExternalLink } from "lucide-react";
import { clsx } from "clsx";
import { API_BASE } from "@/lib/api";

type Row = {
  asset: string;
  insight: string;
  type: "bullish" | "bearish" | "risk";
  confidence: number;
  source?: string;
  link?: string;
};

export default function SignalInsights() {
  const [insights, setInsights] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/radar/opportunities`)
      .then((r) => r.json())
      .then((j) => {
        const sigs = j.signals || [];
        const rows: Row[] = sigs.slice(0, 6).map(
          (s: {
            ticker?: string;
            description?: string;
            signal_type?: string;
            confidence?: number;
            action_hint?: string;
            source?: string;
            metadata?: { link?: string };
          }) => {
            const ah = (s.action_hint || "").toUpperCase();
            let t: Row["type"] = "bullish";
            if (ah.includes("RISK") || ah.includes("AVOID")) t = "risk";
            else if (ah.includes("SELL") || ah.includes("BEAR")) t = "bearish";
            return {
              asset: s.ticker || "MARKET",
              insight: (s.description || s.signal_type || "").slice(0, 200),
              type: t,
              confidence: Math.round((s.confidence || 0.5) * 100),
              source: s.source,
              link: s.metadata?.link,
            };
          }
        );
        startTransition(() =>
          setInsights(
            rows.length
              ? rows
              : [{ asset: "Radar", insight: "No signals yet — wait for scheduler.", type: "risk", confidence: 40 }]
          )
        );
      })
      .catch(() =>
        startTransition(() =>
          setInsights([{ asset: "API", insight: "Backend offline — start FastAPI backend.", type: "risk", confidence: 0 }])
        )
      )
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="bg-slate-900/80 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50 shadow-2xl h-full flex flex-col relative overflow-hidden">
      <div className="absolute -top-10 -right-10 w-40 h-40 bg-violet-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="flex items-center justify-between mb-4 z-10 relative">
        <h2 className="text-lg font-bold text-white flex items-center tracking-tight">
          <div className="w-7 h-7 rounded-lg bg-violet-500/20 flex items-center justify-center mr-2.5 border border-violet-500/30">
            <Target className="w-4 h-4 text-violet-400" />
          </div>
          Opportunity Radar
        </h2>
        <span className="text-[10px] font-bold text-violet-400 bg-violet-500/10 border border-violet-500/20 px-2 py-1 rounded-full uppercase tracking-widest">Live</span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar pr-1 z-10 relative">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-32 space-y-3">
            <div className="w-8 h-8 border-4 border-violet-500/30 border-t-violet-500 rounded-full animate-spin" />
            <p className="text-xs text-slate-500">Scanning ET Markets + NSE feeds...</p>
          </div>
        ) : (
          insights.map((item, idx) => (
            <div key={idx} className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/30 hover:border-slate-600/50 transition-colors flex flex-col space-y-2">
              <div className="flex justify-between items-start">
                <span className="font-bold text-slate-100 text-sm">{item.asset}</span>
                <span className={clsx(
                  "text-[10px] px-2 py-0.5 rounded-full flex items-center font-bold uppercase tracking-wider",
                  item.type === "bullish" ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/20"
                    : item.type === "bearish" ? "bg-red-500/20 text-red-400 border border-red-500/20"
                    : "bg-amber-500/20 text-amber-400 border border-amber-500/20"
                )}>
                  {item.type === "risk" ? <AlertCircle className="w-2.5 h-2.5 mr-1" /> : <Activity className="w-2.5 h-2.5 mr-1" />}
                  {item.type.toUpperCase()}
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{item.insight}</p>
              <div className="w-full bg-slate-700/50 rounded-full h-1.5">
                <div
                  className={clsx("h-1.5 rounded-full transition-all duration-700",
                    item.type === "bullish" ? "bg-emerald-500" : item.type === "bearish" ? "bg-red-500" : "bg-amber-500"
                  )}
                  style={{ width: `${Math.min(100, item.confidence)}%` }}
                />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] text-slate-500 font-medium">CONFIDENCE {item.confidence}%</span>
                {item.link && (
                  <a href={item.link} target="_blank" rel="noopener noreferrer" className="text-[10px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors">
                    Source <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                )}
                {item.source && !item.link && (
                  <span className="text-[10px] text-slate-600">{item.source}</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
