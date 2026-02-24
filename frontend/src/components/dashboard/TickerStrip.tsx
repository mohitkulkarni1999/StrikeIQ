"use client";
import React from 'react';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { CARD } from './DashboardTypes';
import type { LiveMarketData } from '../../hooks/useLiveMarketData';

interface TickerStripProps {
    symbol: string;
    data: LiveMarketData | null;
    effectiveSpot: number | null;
    mode: string;
    status: { market_status?: string } | null;
    modeLabel: string;
    modeColor: string;
}

export function TickerStrip({ symbol, data, effectiveSpot, mode, status, modeLabel, modeColor }: TickerStripProps) {
    const changePositive = (data?.change ?? 0) >= 0;

    return (
        <div
            id="section-dashboard"
            className="rounded-2xl px-4 sm:px-6 py-3 sm:py-4 scroll-mt-20"
            style={{ ...CARD, border: '1px solid rgba(0,229,255,0.10)' }}
        >
            {/* Top accent */}
            <div
                className="h-[1px] w-full mb-3 rounded-full"
                style={{ background: 'linear-gradient(90deg, transparent, rgba(0,229,255,0.50), transparent)' }}
            />

            <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
                {/* Symbol + live dot */}
                <div className="flex items-center gap-2">
                    {mode === 'live' && (
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-70" />
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-400" />
                        </span>
                    )}
                    <span
                        className="text-lg sm:text-xl font-black tracking-widest"
                        style={{
                            background: 'linear-gradient(90deg, #00E5FF, #818cf8)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            fontFamily: "'Space Grotesk', sans-serif",
                        }}
                    >
                        {symbol}
                    </span>
                </div>

                {/* Spot price */}
                <div className="flex items-baseline gap-2">
                    <span
                        className="text-2xl sm:text-3xl font-black tabular-nums"
                        style={{ color: '#fff', fontFamily: "'Space Grotesk', sans-serif" }}
                    >
                        {effectiveSpot?.toFixed(2) ?? '0.00'}
                    </span>
                    {mode === 'snapshot' && (
                        <span
                            className="text-[10px] font-mono px-2 py-0.5 rounded-full"
                            style={{ color: '#60a5fa', background: 'rgba(59,130,246,0.10)', border: '1px solid rgba(59,130,246,0.22)' }}
                        >
                            REST
                        </span>
                    )}
                </div>

                {/* Change */}
                <div
                    className="flex items-center gap-1 text-sm font-mono font-bold tabular-nums"
                    style={{ color: changePositive ? '#4ade80' : '#f87171' }}
                >
                    {changePositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    {changePositive ? '+' : ''}{data?.change_percent?.toFixed(2) ?? '0.00'}%
                </div>

                <div className="flex-1 hidden sm:block" />

                {/* Market status */}
                {status?.market_status && (
                    <div
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-mono font-bold"
                        style={
                            status.market_status === 'OPEN'
                                ? { background: 'rgba(34,197,94,0.10)', border: '1px solid rgba(34,197,94,0.28)', color: '#4ade80' }
                                : status.market_status === 'PRE_OPEN'
                                    ? { background: 'rgba(234,179,8,0.10)', border: '1px solid rgba(234,179,8,0.28)', color: '#facc15' }
                                    : { background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.22)', color: '#f87171' }
                        }
                    >
                        <span
                            className="w-1.5 h-1.5 rounded-full"
                            style={{
                                background: status.market_status === 'OPEN' ? '#4ade80' : status.market_status === 'PRE_OPEN' ? '#facc15' : '#f87171',
                                boxShadow: status.market_status === 'OPEN' ? '0 0 6px #4ade80' : 'none',
                            }}
                        />
                        {status.market_status}
                    </div>
                )}

                {/* Engine mode */}
                <div
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-mono font-bold"
                    style={{
                        background: mode === 'live' ? 'rgba(34,197,94,0.08)' : mode === 'snapshot' ? 'rgba(59,130,246,0.08)' : 'rgba(255,255,255,0.04)',
                        border: `1px solid ${modeColor}30`,
                        color: modeColor,
                    }}
                >
                    <Activity className="w-3 h-3" />
                    {modeLabel}
                </div>
            </div>
        </div>
    );
}
