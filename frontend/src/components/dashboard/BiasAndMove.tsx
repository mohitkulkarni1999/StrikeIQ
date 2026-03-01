"use client";
import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { CARD, CARD_HOVER_BORDER } from './DashboardTypes';
import { SectionLabel } from './StatCards';
import type { LiveMarketData } from '../../hooks/useLiveMarketData';

interface BiasAndMoveProps {
    data: LiveMarketData | null;
    isSnapshotMode: boolean;
}

export function BiasAndMove({ data, isSnapshotMode }: BiasAndMoveProps) {
    const biasLabel = (data as any)?.intelligence?.bias?.label;
    const biasScore = (data as any)?.intelligence?.bias?.score ?? 0;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 sm:gap-4">

            {/* Market Bias card */}
            <div
                className="lg:col-span-4 rounded-2xl p-4 sm:p-5 transition-all duration-300"
                style={CARD}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = CARD_HOVER_BORDER)}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.07)')}
            >
                <div className="flex items-center justify-between mb-4">
                    <SectionLabel>Market Bias</SectionLabel>
                    <span
                        className="text-[11px] font-mono font-bold px-2.5 py-1 rounded-full"
                        style={
                            biasLabel === 'BULLISH'
                                ? { background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.28)', color: '#4ade80' }
                                : biasLabel === 'BEARISH'
                                    ? { background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.28)', color: '#f87171' }
                                    : { background: 'rgba(148,163,184,0.08)', border: '1px solid rgba(148,163,184,0.18)', color: '#94a3b8' }
                        }
                    >
                        {biasLabel ?? 'HOLD'}
                    </span>
                </div>

                {/* Strength bar */}
                <div className="mb-4">
                    <div className="flex justify-between text-[10px] font-mono mb-1.5" style={{ color: 'rgba(148,163,184,0.55)' }}>
                        <span>Strength Score</span>
                        <span className="text-white">{biasScore.toFixed(1)}</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                        <div
                            className="h-full rounded-full transition-all duration-700"
                            style={{
                                width: `${Math.abs(biasScore) * 10}%`,
                                height: '6px',
                                borderRadius: '3px',
                                background: biasLabel === 'BULLISH'
                                    ? 'linear-gradient(90deg, #166534, #4ade80)'
                                    : biasLabel === 'BEARISH'
                                        ? 'linear-gradient(90deg, #991b1b, #f87171)'
                                        : 'linear-gradient(90deg, #334155, #94a3b8)',
                            }}
                        />
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                    {[
                        { label: 'Confidence', value: Math.abs(biasScore) > 0.7 ? 'HIGH' : Math.abs(biasScore) > 0.4 ? 'MED' : 'LOW' },
                        { label: 'Pressure', value: biasLabel === 'BULLISH' ? 'BUYING' : biasLabel === 'BEARISH' ? 'SELLING' : 'BALANCED' },
                    ].map(({ label, value }) => (
                        <div
                            key={label}
                            className="rounded-xl px-3 py-2.5"
                            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
                        >
                            <div className="text-[10px] font-mono mb-0.5" style={{ color: 'rgba(148,163,184,0.5)' }}>{label}</div>
                            <div className="text-[12px] font-mono font-bold text-white">{value}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Expected Move Range Bar */}
            <div
                className="lg:col-span-8 rounded-2xl p-4 sm:p-5 transition-all duration-300"
                style={CARD}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = CARD_HOVER_BORDER)}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.07)')}
            >
                <div className="flex items-center justify-between mb-4">
                    <SectionLabel>Expected Move Range</SectionLabel>
                    {isSnapshotMode && (
                        <span
                            className="text-[10px] font-mono px-2 py-0.5 rounded-full"
                            style={{ color: '#60a5fa', background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.20)' }}
                        >
                            REST Premiums
                        </span>
                    )}
                </div>

                <div className="flex items-center gap-3 mb-3">
                    <span className="text-sm font-mono font-bold tabular-nums w-24 shrink-0 text-red-400">
                        {(((data as any)?.spot ?? 0) - ((data as any)?.intelligence?.probability?.expected_move ?? 0)).toFixed(2)}
                    </span>
                    <div
                        className="flex-1 relative h-5 rounded-full overflow-hidden"
                        style={{ background: 'rgba(0,0,0,0.30)', border: '1px solid rgba(255,255,255,0.07)' }}
                    >
                        <div className="absolute inset-y-0 left-0 right-0 rounded-full" style={{ background: 'linear-gradient(90deg, rgba(239,68,68,0.25), rgba(99,102,241,0.15) 50%, rgba(34,197,94,0.25))' }} />
                        <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 flex items-center">
                            <div className="w-3.5 h-3.5 rounded-full bg-white border-2" style={{ borderColor: '#080b10', boxShadow: '0 0 10px rgba(255,255,255,0.7)' }} />
                        </div>
                    </div>
                </div>
                <div className="flex justify-between text-[10px] font-mono px-1 mb-4" style={{ color: 'rgba(148,163,184,0.50)' }}>
                    <span>↓ Lower bound</span>
                    <span className="text-white">Spot: {(((data as any)?.spot ?? 0).toFixed(2)) ?? '—'}</span>
                    <span>Upper bound ↑</span>
                </div>

                <div className="flex items-center gap-3 mb-3">
                    <span className="text-sm font-mono font-bold tabular-nums w-24 shrink-0 text-green-400">
                        {(((data as any)?.spot ?? 0) + ((data as any)?.intelligence?.probability?.expected_move ?? 0)).toFixed(2)}
                    </span>
                    <div
                        className="flex-1 relative h-5 rounded-full overflow-hidden"
                        style={{ background: 'rgba(0,0,0,0.30)', border: '1px solid rgba(255,255,255,0.07)' }}
                    >
                        <div className="absolute inset-y-0 left-0 right-0 rounded-full" style={{ background: 'linear-gradient(90deg, rgba(239,68,68,0.25), rgba(99,102,241,0.15) 50%, rgba(34,197,94,0.25))' }} />
                        <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 flex items-center">
                            <div className="w-3.5 h-3.5 rounded-full bg-white border-2" style={{ borderColor: '#080b10', boxShadow: '0 0 10px rgba(255,255,255,0.7)' }} />
                        </div>
                    </div>
                </div>

                <div
                    className="inline-flex items-center gap-2 text-[11px] font-mono px-3 py-1.5 rounded-xl"
                    style={{ background: 'rgba(251,146,60,0.08)', border: '1px solid rgba(251,146,60,0.22)', color: '#fb923c' }}
                >
                    <AlertTriangle className="w-3.5 h-3.5" />
                    BREAKOUT RISK: {(((data as any)?.intelligence?.probability?.breach_probability?.toFixed(0)) ?? '0')}%
                </div>
            </div>
        </div>
    );
}
