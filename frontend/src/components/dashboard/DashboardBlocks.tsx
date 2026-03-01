"use client";
import React from 'react';
import { WifiOff, Database } from 'lucide-react';
import { CARD } from './DashboardTypes';

export function LoadingBlock() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
            <div className="relative mb-6">
                <div
                    className="w-16 h-16 rounded-full border-2 animate-spin"
                    style={{ borderColor: 'rgba(0,229,255,0.15)', borderTopColor: '#00E5FF' }}
                />
                <div className="absolute inset-0 flex items-center justify-center">
                    <div
                        className="w-8 h-8 rounded-full border-2 animate-spin"
                        style={{ borderColor: 'rgba(124,58,237,0.2)', borderTopColor: '#7C3AED', animationDirection: 'reverse' }}
                    />
                </div>
            </div>
            <p
                className="text-sm font-mono animate-pulse tracking-widest uppercase"
                style={{ color: 'rgba(0,229,255,0.8)', fontFamily: "'JetBrains Mono', monospace" }}
            >
                Synchronizing…
            </p>
            <p className="text-xs mt-2" style={{ color: 'rgba(148,163,184,0.4)', fontFamily: "'JetBrains Mono', monospace" }}>
                Connecting to market feed
            </p>
        </div>
    );
}

export function SnapshotReadyBlock() {
    return (
        <div
            className="flex flex-col items-center justify-center min-h-[40vh] mx-4 my-6 p-8 rounded-2xl"
            style={{ ...CARD, border: '1px solid rgba(59,130,246,0.20)' }}
        >
            <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
                style={{ background: 'rgba(59,130,246,0.10)', border: '1px solid rgba(59,130,246,0.25)' }}
            >
                <Database className="w-7 h-7 text-blue-400" />
            </div>
            <h3 className="text-lg font-bold text-blue-300 tracking-wide mb-2">Snapshot Mode Active</h3>
            <p className="text-sm text-center max-w-md leading-relaxed mb-4" style={{ color: 'rgba(148,163,184,0.6)' }}>
                Using REST snapshot data — market is currently closed
            </p>
            <div
                className="px-4 py-1.5 rounded-full text-xs font-mono font-bold"
                style={{ background: 'rgba(59,130,246,0.10)', border: '1px solid rgba(59,130,246,0.22)', color: '#60a5fa' }}
            >
                SNAPSHOT MODE
            </div>
        </div>
    );
}

export function ErrorBlock({ message }: { message: string }) {
    return (
        <div
            className="flex flex-col items-center justify-center min-h-[40vh] mx-4 my-6 p-8 rounded-2xl"
            style={{ ...CARD, border: '1px solid rgba(239,68,68,0.18)' }}
        >
            <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
                style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.22)' }}
            >
                <WifiOff className="w-7 h-7 text-red-400" />
            </div>
            <h3 className="text-lg font-bold text-red-300 tracking-wide mb-2">Connection Interrupted</h3>
            <p className="text-sm text-center max-w-md leading-relaxed mb-4" style={{ color: 'rgba(148,163,184,0.6)' }}>
                {message}
            </p>
            <div
                className="px-4 py-1.5 rounded-full text-xs font-mono font-bold"
                style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.22)', color: '#f87171' }}
            >
                OFFLINE
            </div>
        </div>
    );
}
