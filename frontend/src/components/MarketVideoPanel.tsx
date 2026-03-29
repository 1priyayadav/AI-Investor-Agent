"use client";
import { useState } from "react";
import { API_BASE, authHeaders } from "@/lib/api";
import { Film, Sparkles, Clock, BarChart2 } from "lucide-react";

export default function MarketVideoPanel() {
  const [loading, setLoading] = useState(false);
  const [loadStep, setLoadStep] = useState(0);
  const [url, setUrl] = useState<string | null>(null);
  const [meta, setMeta] = useState<{ duration?: number; patterns?: number; fiidii?: boolean } | null>(null);
  const [err, setErr] = useState("");

  const STEPS = ["Scanning NSE universe…", "Building FII/DII frame…", "Rendering race chart…", "Encoding video…"];

  async function generate() {
    setErr("");
    setLoading(true);
    setLoadStep(0);
    setUrl(null);
    setMeta(null);
    // Cycle through step labels every 20 seconds
    const stepInterval = setInterval(() => setLoadStep((s) => (s + 1) % STEPS.length), 20000);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 180000);
    try {
      const res = await fetch(`${API_BASE}/api/v1/video/daily-wrap`, {
        method: "POST",
        headers: authHeaders(),
        signal: controller.signal,
      });
      clearTimeout(timeout);
      clearInterval(stepInterval);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Video generation failed");
      setUrl(`${API_BASE}${data.url_path}`);
      setMeta({
        duration: data.duration_estimate_sec,
        patterns: data.patterns_sampled,
        fiidii: data.fiidii_present,
      });
    } catch (e: unknown) {
      clearTimeout(timeout);
      clearInterval(stepInterval);
      if (e instanceof Error && e.name === "AbortError") {
        setErr("Timed out after 3 minutes — try again, cached patterns will load faster.");
      } else {
        setErr(e instanceof Error ? e.message : "Failed to generate video");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-slate-900/80 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50 shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 w-48 h-48 bg-amber-500/10 rounded-full blur-[80px] pointer-events-none"></div>

      <div className="flex items-center justify-between mb-4 z-10 relative">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2.5 tracking-tight mb-1">
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center shadow-[0_0_15px_rgba(245,158,11,0.2)]">
              <Film className="w-4 h-4 text-amber-400" />
            </div>
            AI Market Video Engine
          </h3>
          <p className="text-xs text-slate-400 ml-11">
            Auto-generates 30–90s MP4: ET-style title → FII/DII flows → NSE pattern race chart → IPO tracker. Zero manual editing.
          </p>
        </div>
        <button
          type="button"
          onClick={generate}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 disabled:opacity-50 transition-all font-semibold text-sm shadow-lg hover:shadow-amber-500/20"
        >
          {loading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-amber-400/30 border-t-amber-400 rounded-full animate-spin" />
              {STEPS[loadStep]}
            </>
          ) : (
            <>
              <Sparkles className="w-3.5 h-3.5" />
              Generate Daily Wrap
            </>
          )}
        </button>
      </div>

      {/* Feature tags */}
      <div className="flex flex-wrap gap-2 mb-4 ml-11 z-10 relative">
        {["Race-chart simulator", "FII/DII visualization", "NSE pattern scan", "IPO tracker", "Sector rotation"].map((tag) => (
          <span key={tag} className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-md bg-slate-800/60 border border-slate-700/40 text-slate-400">
            {tag}
          </span>
        ))}
      </div>

      {err && (
        <div className="mt-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm z-10 relative">
          {err}
        </div>
      )}

      {meta && (
        <div className="mt-3 flex flex-wrap gap-4 z-10 relative">
          {meta.duration && (
            <div className="flex items-center gap-1.5 text-slate-400 text-xs">
              <Clock className="w-3.5 h-3.5 text-amber-400" />
              <span>~{Math.round(meta.duration)}s video</span>
            </div>
          )}
          {meta.patterns !== undefined && (
            <div className="flex items-center gap-1.5 text-slate-400 text-xs">
              <BarChart2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>{meta.patterns} NSE patterns sampled</span>
            </div>
          )}
          <div className={`flex items-center gap-1.5 text-xs ${meta.fiidii ? "text-emerald-400" : "text-slate-500"}`}>
            <span className={`w-2 h-2 rounded-full ${meta.fiidii ? "bg-emerald-400" : "bg-slate-600"}`}></span>
            <span>FII/DII live data {meta.fiidii ? "included" : "unavailable"}</span>
          </div>
        </div>
      )}

      {url && (
        <div className="mt-4 z-10 relative">
          <video
            className="w-full rounded-xl border border-slate-700/50 shadow-xl"
            controls
            src={url}
          />
          <a
            href={url}
            download
            className="mt-2 flex items-center justify-center gap-2 text-xs text-slate-400 hover:text-white transition-colors"
          >
            Download MP4
          </a>
        </div>
      )}
    </div>
  );
}
