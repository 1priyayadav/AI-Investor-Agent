"use client";
import { useState } from 'react';
import { Send, Bot, User, Network, BookOpen } from 'lucide-react';

interface Msg {
    role: "agent" | "user";
    text: string;
    sources?: string[];
}

export default function ChatInterface() {
    const [messages, setMessages] = useState<Msg[]>([
        {
            role: 'agent',
            text: 'I am your Financial Orchestrator Agent. I run a full 11-step analysis: ET Markets + NSE data ingestion → signal detection → technical patterns → RAG context → portfolio impact → backtesting → recommendation.\n\nAsk me anything: "Should I buy Reliance?" or "Explain Infosys signals."',
            sources: ["ET Markets RSS", "NSE public feeds", "ChromaDB RAG", "Neo4j graph"]
        }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSend = async () => {
        if (!input.trim()) return;
        const userText = input;
        setMessages(p => [...p, { role: 'user', text: userText }]);
        setInput('');
        setLoading(true);

        try {
            const res = await fetch("http://localhost:8000/api/v1/chat/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userText })
            });
            const data = await res.json();
            setMessages(p => [...p, {
                role: 'agent',
                text: data.reply,
                sources: data.sources || []
            }]);
        } catch (e) {
            console.error(e);
            setMessages(p => [...p, {
                role: 'agent',
                text: 'Backend is offline. Please start the FastAPI server:\n`python -m uvicorn backend.main:app --reload --port 8000`',
                sources: []
            }]);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="bg-slate-900/80 backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-2xl flex flex-col h-[600px] overflow-hidden relative">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-emerald-500 to-amber-500"></div>

            <div className="p-5 border-b border-slate-800/50 bg-slate-900/40 flex items-center justify-between z-10">
                <div className="flex items-center font-bold text-white text-lg tracking-tight">
                    <div className="p-2 bg-indigo-500/20 rounded-lg mr-3 border border-indigo-500/30 text-indigo-400">
                        <Network className="w-5 h-5" />
                    </div>
                    Market ChatGPT
                </div>
                <div className="text-xs text-slate-500 font-medium">11-agent pipeline · portfolio-aware</div>
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-5 bg-slate-950/20 relative custom-scrollbar">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(99,102,241,0.04),transparent_70%)] pointer-events-none"></div>

                {messages.map((m, i) => (
                    <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} relative z-10`}>
                        <div className={`flex max-w-[88%] ${m.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                            <div className={`w-9 h-9 rounded-xl flex flex-shrink-0 items-center justify-center shadow-lg ${m.role === 'user' ? 'bg-indigo-600 ml-3' : 'bg-slate-800 border border-emerald-500/30 mr-3'}`}>
                                {m.role === 'user' ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-emerald-400" />}
                            </div>
                            <div className="flex flex-col gap-2">
                                <div className={`p-4 rounded-xl text-sm leading-relaxed shadow-sm ${m.role === 'user' ? 'bg-indigo-600/90 text-white rounded-tr-none' : 'bg-slate-800/80 text-slate-200 border border-slate-700/50 rounded-tl-none'}`}>
                                    {m.text.split('\n').map((line, k) => (
                                        <p key={k} className="mb-1.5 last:mb-0">{line.replace(/\*\*/g, "")}</p>
                                    ))}
                                </div>

                                {/* Source Citations — the key missing piece */}
                                {m.role === 'agent' && m.sources && m.sources.length > 0 && (
                                    <div className="flex flex-wrap gap-1.5 ml-1">
                                        <BookOpen className="w-3 h-3 text-slate-500 mt-0.5 flex-shrink-0" />
                                        {m.sources.map((src, si) => (
                                            <span key={si} className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800/60 border border-slate-700/40 text-slate-400 font-medium">
                                                {src}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="flex justify-start relative z-10">
                        <div className="w-9 h-9 rounded-xl bg-slate-800 border border-emerald-500/30 mr-3 flex items-center justify-center flex-shrink-0">
                            <Bot className="w-4 h-4 text-emerald-400" />
                        </div>
                        <div className="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/50 rounded-tl-none flex items-center gap-2">
                            <span className="text-xs text-slate-400 mr-2">Running 11-agent pipeline...</span>
                            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-[bounce_1s_infinite]"></span>
                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-[bounce_1s_infinite_0.2s]"></span>
                            <span className="w-2 h-2 rounded-full bg-amber-500 animate-[bounce_1s_infinite_0.4s]"></span>
                        </div>
                    </div>
                )}
            </div>

            <div className="p-4 border-t border-slate-800/50 bg-slate-900/60 z-10">
                <div className="relative flex items-center">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        className="w-full bg-slate-950/50 text-white rounded-xl pl-5 pr-14 py-3.5 border border-slate-700/80 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50 transition-all text-sm"
                        placeholder='Try: "Should I hold Reliance?" or "Analyse Infosys signals"'
                    />
                    <button
                        onClick={handleSend}
                        className="absolute right-2.5 p-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-white transition-all disabled:opacity-40"
                        disabled={loading || !input.trim()}
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}
