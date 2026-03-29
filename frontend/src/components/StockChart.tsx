"use client";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { useState, useEffect } from "react";
import { API_BASE } from "@/lib/api";
import { TrendingUp, ChevronDown } from "lucide-react";

const SYMBOLS = [
  { label: "RELIANCE", value: "RELIANCE.NS" },
  { label: "INFY", value: "INFY.NS" },
  { label: "ICICI Bank", value: "ICICIBANK.NS" },
  { label: "TCS", value: "TCS.NS" },
  { label: "SBI", value: "SBIN.NS" },
];

export default function StockChart() {
  const [data, setData] = useState<{ date: string; close: number }[]>([]);
  const [sym, setSym] = useState(SYMBOLS[0].value);
  const [loading, setLoading] = useState(true);
  const [change, setChange] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/api/v1/market/ohlcv?symbol=${encodeURIComponent(sym)}&period=6mo`)
      .then((r) => r.json())
      .then((j) => {
        const s = j.series || [];
        const mapped = s.map((row: { date: string; close: number }) => ({
          date: row.date,
          close: row.close,
        }));
        setData(mapped);
        if (mapped.length >= 2) {
          const first = mapped[0].close;
          const last = mapped[mapped.length - 1].close;
          setChange(((last - first) / first) * 100);
        }
      })
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [sym]);

  const positive = change === null || change >= 0;

  return (
    <div className="bg-slate-900/80 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50 shadow-2xl h-full flex flex-col relative overflow-hidden">
      <div className="absolute -bottom-16 -left-16 w-48 h-48 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="flex justify-between items-start mb-4 z-10 relative">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center tracking-tight mb-1">
            <TrendingUp className="w-4 h-4 mr-2 text-blue-400" /> NSE Live Chart
          </h2>
          {change !== null && (
            <span className={`text-xs font-bold px-2 py-0.5 rounded ${positive ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
              {positive ? "+" : ""}{change.toFixed(2)}% (6mo)
            </span>
          )}
        </div>
        <div className="relative">
          <select
            value={sym}
            onChange={(e) => setSym(e.target.value)}
            className="appearance-none bg-slate-800/80 border border-slate-700/50 text-sm text-white rounded-lg px-3 py-2 pr-8 cursor-pointer outline-none focus:border-blue-500 transition-colors"
          >
            {SYMBOLS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
          <ChevronDown className="absolute right-2 top-2.5 w-4 h-4 text-slate-400 pointer-events-none" />
        </div>
      </div>

      <div className="flex-1 w-full min-h-[200px] min-w-0 z-10 relative">
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <div className="w-8 h-8 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
          </div>
        ) : data.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-500 text-sm">No data available</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={positive ? "#10b981" : "#f43f5e"} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={positive ? "#10b981" : "#f43f5e"} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="date" stroke="#64748b" tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} minTickGap={24} />
              <YAxis stroke="#64748b" tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={false} domain={["auto", "auto"]} />
              <Tooltip
                contentStyle={{ backgroundColor: "rgba(15,23,42,0.95)", backdropFilter: "blur(12px)", border: "1px solid #334155", borderRadius: "10px", color: "#f8fafc" }}
                itemStyle={{ color: positive ? "#10b981" : "#f43f5e", fontWeight: "bold" }}
              />
              <Area type="monotone" dataKey="close" stroke={positive ? "#10b981" : "#f43f5e"} strokeWidth={2} fillOpacity={1} fill="url(#colorPrice)" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
