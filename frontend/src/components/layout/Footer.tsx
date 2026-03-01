"use client";

import React, { useEffect, useState } from 'react';
import api from '../../api/axios';

const OPEN_STATES = ['OPEN', 'PRE_OPEN', 'OPENING_END'];

export interface FooterProps {
    onSymbolSelect?: (sym: string) => void;
}

export default function Footer({ onSymbolSelect }: FooterProps) {
    const [marketStatus, setMarketStatus] = useState<string | null>(null);
    const [statusResolved, setStatusResolved] = useState(false);

    useEffect(() => {
        const fetch = async () => {
            try {
                const res = await api.get('/api/v1/market/session');
                const ms = res.data?.data?.market_status ?? res.data?.market_status ?? null;
                setMarketStatus(ms);
            } catch {
                setMarketStatus(null);
            } finally {
                setStatusResolved(true);
            }
        };
        fetch();
        const id = setInterval(fetch, 60_000);
        return () => clearInterval(id);
    }, []);

    const marketOpen = marketStatus ? OPEN_STATES.includes(marketStatus) : false;

    const MARKETS = [
        { sym: 'NIFTY', desc: 'Nifty 50 Index' },
        { sym: 'BANKNIFTY', desc: 'Bank Nifty Index' },
        { sym: 'FINNIFTY', desc: 'Fin Nifty Index' },
    ];

    const SYSTEM_ROWS = [
        { label: 'Data Source', value: 'Upstox API' },
        { label: 'Exchange', value: 'NSE India' },
        { label: 'Market Hours', value: '09:15 – 15:30 IST' },
        { label: 'Settlement', value: 'T+1 Rolling' },
    ];

    return (
        <footer className="relative z-10 mt-8">

            {/* ── Glow separator ──────────────────────────────────────────────── */}
            <div className="relative h-px">
                <div
                    className="absolute inset-0"
                    style={{
                        background:
                            'linear-gradient(90deg, transparent 0%, rgba(0,229,255,0.40) 35%, rgba(124,58,237,0.40) 65%, transparent 100%)',
                    }}
                />
                <div
                    className="absolute left-1/2 -translate-x-1/2 -top-2 w-48 h-5"
                    style={{
                        background: 'radial-gradient(ellipse, rgba(0,229,255,0.22) 0%, transparent 70%)',
                        filter: 'blur(4px)',
                    }}
                />
            </div>

            {/* ── Body ────────────────────────────────────────────────────────── */}
            <div
                className="backdrop-blur-2xl"
                style={{ background: 'rgba(8,11,22,0.92)' }}
            >
                <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-10">

                    {/* ── Main grid ─────────────────────────────────────────────── */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 py-8 border-b" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>

                        {/* Brand */}
                        <div className="sm:col-span-1">
                            {/* Logo */}
                            <div className="flex items-center gap-2.5 mb-3">
                                <div
                                    className="flex items-center justify-center w-8 h-8 rounded-xl shrink-0"
                                    style={{
                                        background: 'linear-gradient(135deg, rgba(0,229,255,0.16) 0%, rgba(124,58,237,0.10) 100%)',
                                        border: '1px solid rgba(0,229,255,0.22)',
                                        boxShadow: '0 0 16px rgba(0,229,255,0.12)',
                                    }}
                                >
                                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                                        <path d="M2 12L6 6L9 9L13 3" stroke="#00E5FF" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                                        <circle cx="13" cy="3" r="1.4" fill="#00E5FF" />
                                        <path d="M2 14H14" stroke="#7C3AED" strokeWidth="1.2" strokeLinecap="round" opacity="0.7" />
                                    </svg>
                                </div>
                                <div>
                                    <div
                                        className="text-base font-black tracking-tight leading-none"
                                        style={{
                                            background: 'linear-gradient(90deg, #00E5FF 0%, #818cf8 55%, #a78bfa 100%)',
                                            WebkitBackgroundClip: 'text',
                                            WebkitTextFillColor: 'transparent',
                                            fontFamily: "'Space Grotesk', sans-serif",
                                        }}
                                    >
                                        StrikeIQ
                                    </div>
                                    <div
                                        className="text-[8px] tracking-[0.22em] uppercase mt-0.5"
                                        style={{ color: 'rgba(129,140,248,0.50)', fontFamily: "'JetBrains Mono', monospace" }}
                                    >
                                        Options Intelligence
                                    </div>
                                </div>
                            </div>

                            {/* Tagline */}
                            <p
                                className="text-[11px] leading-relaxed mb-4"
                                style={{ color: 'rgba(148,163,184,0.45)', fontFamily: "'Space Grotesk', sans-serif" }}
                            >
                                AI-powered derivatives intelligence for Indian markets — neural regime detection &amp; institutional flow analysis.
                            </p>

                            {/* Pills */}
                            <div className="flex flex-wrap gap-1.5">
                                {[
                                    { label: 'NSE India', color: '#4ade80' },
                                    { label: 'Upstox API', color: '#60a5fa' },
                                    { label: 'WebSocket', color: '#a78bfa' },
                                    { label: 'AI Engine', color: '#fb923c' },
                                ].map(({ label, color }) => (
                                    <span
                                        key={label}
                                        className="text-[9px] font-mono px-2 py-0.5 rounded-full"
                                        style={{
                                            background: `${color}10`,
                                            border: `1px solid ${color}22`,
                                            color,
                                            letterSpacing: '0.05em',
                                        }}
                                    >
                                        {label}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Markets */}
                        <div>
                            <div
                                className="text-[9px] font-bold tracking-[0.22em] uppercase mb-3"
                                style={{ color: 'rgba(0,229,255,0.45)', fontFamily: "'JetBrains Mono', monospace" }}
                            >
                                Markets
                            </div>
                            <ul className="space-y-1">
                                {MARKETS.map(({ sym, desc }) => (
                                    <li key={sym}>
                                        <button
                                            onClick={() => onSymbolSelect?.(sym)}
                                            className="group flex items-center gap-2 w-full py-1.5 rounded-lg px-2 transition-all duration-150 text-left"
                                            style={{ background: 'transparent' }}
                                            onMouseEnter={(e) => {
                                                e.currentTarget.style.background = 'rgba(0,229,255,0.04)';
                                            }}
                                            onMouseLeave={(e) => {
                                                e.currentTarget.style.background = 'transparent';
                                            }}
                                        >
                                            <span
                                                className="w-1 h-1 rounded-full shrink-0 transition-all group-hover:bg-[#00E5FF]"
                                                style={{ background: 'rgba(148,163,184,0.30)' }}
                                            />
                                            <div className="flex flex-col">
                                                <span
                                                    className="text-[11px] font-mono font-semibold leading-none group-hover:text-white transition-colors"
                                                    style={{ color: 'rgba(148,163,184,0.60)', fontFamily: "'JetBrains Mono', monospace" }}
                                                >
                                                    {sym}
                                                </span>
                                                <span
                                                    className="text-[9px] mt-0.5"
                                                    style={{ color: 'rgba(100,116,139,0.40)', fontFamily: "'JetBrains Mono', monospace" }}
                                                >
                                                    {desc}
                                                </span>
                                            </div>
                                            <span
                                                className="ml-auto text-[8px] font-mono opacity-0 group-hover:opacity-100 transition-opacity"
                                                style={{ color: 'rgba(0,229,255,0.50)' }}
                                            >
                                                →
                                            </span>
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* System + Market Status */}
                        <div>
                            <div
                                className="text-[9px] font-bold tracking-[0.22em] uppercase mb-3"
                                style={{ color: 'rgba(124,58,237,0.55)', fontFamily: "'JetBrains Mono', monospace" }}
                            >
                                System
                            </div>
                            <ul className="space-y-2 mb-4">
                                {SYSTEM_ROWS.map(({ label, value }) => (
                                    <li key={label} className="flex items-center justify-between">
                                        <span
                                            className="text-[10px] font-mono"
                                            style={{ color: 'rgba(148,163,184,0.38)', fontFamily: "'JetBrains Mono', monospace" }}
                                        >
                                            {label}
                                        </span>
                                        <span
                                            className="text-[10px] font-mono font-semibold"
                                            style={{ color: 'rgba(100,220,180,0.65)', fontFamily: "'JetBrains Mono', monospace" }}
                                        >
                                            {value}
                                        </span>
                                    </li>
                                ))}
                            </ul>

                            {/* Market status pill */}
                            <div
                                className="flex items-center gap-2 px-3 py-2 rounded-xl"
                                style={{
                                    background: marketOpen ? 'rgba(34,197,94,0.07)' : 'rgba(255,255,255,0.03)',
                                    border: marketOpen ? '1px solid rgba(34,197,94,0.18)' : '1px solid rgba(255,255,255,0.06)',
                                }}
                            >
                                {marketOpen ? (
                                    <span className="relative flex h-1.5 w-1.5 shrink-0">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-60" />
                                        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-green-400" />
                                    </span>
                                ) : (
                                    <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: '#334155' }} />
                                )}
                                <span
                                    className="text-[10px] font-mono font-semibold"
                                    style={{
                                        color: marketOpen ? '#4ade80' : 'rgba(100,116,139,0.50)',
                                        letterSpacing: '0.08em',
                                    }}
                                >
                                    {!statusResolved ? 'CHECKING…' : marketOpen ? 'MARKET OPEN' : 'MARKET CLOSED'}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* ── Bottom bar ────────────────────────────────────────────────── */}
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-2 py-4">
                        <span
                            className="text-[9px] tracking-widest uppercase"
                            style={{ color: 'rgba(100,116,139,0.35)', fontFamily: "'JetBrains Mono', monospace" }}
                        >
                            © 2026 StrikeIQ · All rights reserved
                        </span>

                        <div className="hidden sm:flex items-center gap-2">
                            {['NSE India', 'Upstox', 'Real-time Data'].map((tag, i, arr) => (
                                <React.Fragment key={tag}>
                                    <span
                                        className="text-[9px] font-mono"
                                        style={{ color: 'rgba(100,116,139,0.30)' }}
                                    >
                                        {tag}
                                    </span>
                                    {i < arr.length - 1 && (
                                        <span className="w-0.5 h-0.5 rounded-full" style={{ background: 'rgba(100,116,139,0.25)' }} />
                                    )}
                                </React.Fragment>
                            ))}
                        </div>

                        <span
                            className="text-[9px] tracking-widest uppercase"
                            style={{ color: 'rgba(100,116,139,0.25)', fontFamily: "'JetBrains Mono', monospace" }}
                        >
                            For informational purposes only
                        </span>
                    </div>

                </div>
            </div>
        </footer>
    );
}
