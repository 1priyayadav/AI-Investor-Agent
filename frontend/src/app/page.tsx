"use client";
import { useState } from "react";
import PortfolioDashboard from "@/components/PortfolioDashboard";
import AlertPanel from "@/components/AlertPanel";
import StockChart from "@/components/StockChart";
import ChatInterface from "@/components/ChatInterface";
import SignalInsights from "@/components/SignalInsights";
import MarketVideoPanel from "@/components/MarketVideoPanel";
import LoginBar from "@/components/LoginBar";
import { Activity } from "lucide-react";

export default function Home() {
  const [session, setSession] = useState(0);

  return (
    <main className="min-h-screen p-4 md:p-8 font-sans max-w-[1600px] mx-auto">
      <header className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center">
          <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center mr-4 shadow-lg shadow-indigo-500/20">
            <Activity className="text-white w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">AI Investor Intelligence</h1>
            <p className="text-sm text-slate-400">
              ET Markets data · NSE patterns · Opportunity radar · AI video engine
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <LoginBar onAuth={() => setSession((s) => s + 1)} />
          <div className="px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-full flex items-center">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse mr-2"></span>
            <span className="text-xs font-semibold text-emerald-400">Backend</span>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        <div className="xl:col-span-8 flex flex-col space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <PortfolioDashboard key={`p-${session}`} />
            <StockChart key={`c-${session}`} />
            <SignalInsights key={`i-${session}`} />
          </div>
          <MarketVideoPanel />
          <ChatInterface key={`ch-${session}`} />
        </div>

        <div className="xl:col-span-4 h-[800px] xl:h-auto">
          <AlertPanel />
        </div>
      </div>
    </main>
  );
}
