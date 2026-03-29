"use client";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip } from "recharts";
import { useEffect, useState } from "react";
import { Wallet, TrendingUp } from "lucide-react";
import { API_BASE, authHeaders } from "@/lib/api";

const COLORS = ["#8b5cf6", "#10b981", "#f59e0b", "#f43f5e", "#3b82f6"];

type Exposure = {
  total_value: number;
  pieData: { name: string; value: number }[];
};

export default function PortfolioDashboard() {
  const [data, setData] = useState<Exposure | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/portfolio`, { headers: authHeaders() })
      .then((res) => res.json())
      .then((json) => {
        if (json.sector_exposure && Object.keys(json.sector_exposure).length) {
          const pieData = Object.keys(json.sector_exposure).map((key) => ({
            name: key,
            value: json.sector_exposure[key],
          }));
          setData({ total_value: json.total_value, pieData });
        } else {
          setData({
            total_value: json.total_value ?? 0,
            pieData: [{ name: "Unclassified", value: 100 }],
          });
        }
      })
      .catch(() => {
        setData({
          total_value: 0,
          pieData: [
            { name: "Sign in", value: 50 },
            { name: "Required", value: 50 },
          ],
        });
      });
  }, []);

  if (!data)
    return (
      <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-700/50 shadow-2xl rounded-2xl p-6 h-64 flex flex-col justify-center items-center">
        <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
        <p className="mt-4 text-indigo-400 font-medium tracking-tight">Synchronizing Portfolio...</p>
      </div>
    );

  return (
    <div className="bg-slate-900/80 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50 shadow-2xl relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 rounded-full blur-[80px] pointer-events-none group-hover:bg-emerald-500/20 transition-all duration-700"></div>

      <div className="flex items-center justify-between mb-8 z-10 relative">
        <h2 className="text-xl font-bold text-white flex items-center tracking-tight">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center mr-3 border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
            <Wallet className="w-4 h-4 text-emerald-400" />
          </div>
          Exposure Vault (India)
        </h2>
      </div>

      <div className="flex items-end justify-between mb-8 z-10 relative">
        <div>
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5 opacity-80">
            Total book (INR)
          </p>
          <div className="flex items-center">
            <p className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400 drop-shadow-sm tracking-tight">
              ₹{data.total_value.toLocaleString("en-IN")}
            </p>
            <div className="ml-4 flex items-center bg-emerald-500/10 px-2.5 py-1 rounded text-emerald-400 text-sm font-bold border border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
              <TrendingUp className="w-3.5 h-3.5 mr-1" /> Live
            </div>
          </div>
        </div>
      </div>

      <div className="h-[220px] w-full relative z-10 mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data.pieData}
              innerRadius={70}
              outerRadius={95}
              paddingAngle={8}
              dataKey="value"
              stroke="rgba(0,0,0,0.5)"
              strokeWidth={3}
              cornerRadius={6}
            >
              {data.pieData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[index % COLORS.length]}
                  style={{ filter: "drop-shadow(0px 4px 6px rgba(0,0,0,0.5))" }}
                />
              ))}
            </Pie>
            <RechartsTooltip
              contentStyle={{
                backgroundColor: "rgba(15, 23, 42, 0.95)",
                backdropFilter: "blur(12px)",
                border: "1px solid rgba(16, 185, 129, 0.3)",
                borderRadius: "12px",
                color: "#fff",
                boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
              }}
              itemStyle={{ color: "#fff", fontWeight: "bold" }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 m-auto w-[130px] h-[130px] rounded-full shadow-[inset_0_4px_25px_rgba(0,0,0,0.5)] pointer-events-none"></div>
      </div>

      <div className="mt-8 grid grid-cols-2 gap-y-4 z-10 relative">
        {data.pieData.map((d, i) => (
          <div key={i} className="flex items-center text-sm font-bold text-slate-300">
            <span
              className="w-3.5 h-3.5 rounded-full mr-3 shadow-md border border-white/10"
              style={{ backgroundColor: COLORS[i % COLORS.length] }}
            ></span>
            {d.name}{" "}
            <span className="ml-auto pr-4 text-white opacity-50 font-mono tracking-tighter">
              {d.value}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
