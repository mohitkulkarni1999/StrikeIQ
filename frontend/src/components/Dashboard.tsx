"use client";

import React, { useState, useEffect, memo } from 'react';
import { Activity, Database } from 'lucide-react';
import { useLiveMarketData } from '../hooks/useLiveMarketData';
import { useModeGuard, useEffectiveSpot, useSnapshotAnalytics, useTimeoutProtection } from './SafeModeGuard';
import DebugBadge from './DebugBadge';
import AIInterpretationPanel from './AIInterpretationPanel';
import OIHeatmap from './OIHeatmap';
import AlertPanelFinal from './intelligence/AlertPanelFinal';

// ── Dashboard sub-components ─────────────────────────────────────────────────
import { LoadingBlock, SnapshotReadyBlock, ErrorBlock } from './dashboard/DashboardBlocks';
import { TickerStrip } from './dashboard/TickerStrip';
import { StatCardsRow } from './dashboard/StatCards';
import { BiasAndMove } from './dashboard/BiasAndMove';
import { SmartMoneyAndLiquidity } from './dashboard/SmartMoneyAndLiquidity';
import { CARD } from './dashboard/DashboardTypes';

// ── Memoized heavy panels ─────────────────────────────────────────────────────
const MemoizedOIHeatmap = memo(OIHeatmap);
const MemoizedAIPanel = memo(AIInterpretationPanel);
const MemoizedAlerts = memo(AlertPanelFinal);

// ── Types ─────────────────────────────────────────────────────────────────────
interface DashboardProps { initialSymbol?: string; }

export default function Dashboard({ initialSymbol = 'NIFTY' }: DashboardProps) {
  const [symbol] = useState(initialSymbol);
  const [expiryList, setExpiryList] = useState<string[]>([]);
  const [selectedExpiry, setSelectedExpiry] = useState<string | null>(null);

  const { data, status, error, loading, mode } = useLiveMarketData(symbol, selectedExpiry);

  const isLiveMode = useModeGuard(mode, 'LIVE');
  const isSnapshotMode = useModeGuard(mode, 'SNAPSHOT');
  const effectiveSpot = useEffectiveSpot(data, mode);
  const isAnalyticsEnabled = (data as any)?.analytics_enabled !== false;

  // Add/remove snapshot-mode body class
  React.useEffect(() => {
    if (mode !== 'live') {
      document.body.classList.add('snapshot-mode');
    } else {
      document.body.classList.remove('snapshot-mode');
    }
  }, [mode]);

  // Populate expiry list from data
  useEffect(() => {
    if (data?.available_expiries && data.available_expiries.length > 0) {
      setExpiryList(data.available_expiries);
      if (!selectedExpiry) setSelectedExpiry(data.available_expiries[0]);
    }
  }, [data?.available_expiries, selectedExpiry]);

  const safeError = typeof error === 'string' ? error : null;
  const modeLabel = mode === 'live' ? 'LIVE' : mode === 'snapshot' ? 'SNAPSHOT' : mode === 'error' ? 'HALTED' : 'OFFLINE';
  const modeColor = mode === 'live' ? '#4ade80' : mode === 'snapshot' ? '#60a5fa' : '#f87171';

  // ── State guards ──────────────────────────────────────────────────────────
  if (loading) return mode === 'snapshot' ? <SnapshotReadyBlock /> : <LoadingBlock />;
  if (safeError) return <ErrorBlock message={safeError} />;
  if (mode === 'snapshot' && !data) return <SnapshotReadyBlock />;

  // ── Main render ───────────────────────────────────────────────────────────
  return (
    <div
      className="min-h-screen text-white"
      style={{ background: 'radial-gradient(ellipse 100% 50% at 50% 0%, #0d1117 0%, #080b10 60%)' }}
    >
      {/* Subtle grid overlay */}
      <div
        className="pointer-events-none fixed inset-0 z-0"
        style={{
          backgroundImage: 'linear-gradient(rgba(0,229,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(0,229,255,1) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          opacity: 0.018,
        }}
      />

      <div className="relative z-10 max-w-[1920px] mx-auto px-3 sm:px-5 lg:px-8 py-4 sm:py-6 space-y-4">

        {/* ROW 1 — Ticker strip */}
        <TickerStrip
          symbol={symbol}
          data={data}
          effectiveSpot={effectiveSpot}
          mode={mode}
          status={status}
          modeLabel={modeLabel}
          modeColor={modeColor}
        />

        {/* ROW 2 — Four stat cards */}
        <StatCardsRow data={data} isAnalyticsEnabled={isAnalyticsEnabled} />

        {/* ROW 3 — Market Bias + Expected Move */}
        <BiasAndMove data={data} isSnapshotMode={isSnapshotMode} />

        {/* ROW 4 — Smart Money + Liquidity */}
        <SmartMoneyAndLiquidity
          data={data}
          isLiveMode={isLiveMode}
          isSnapshotMode={isSnapshotMode}
          mode={mode}
        />

        {/* ── Snapshot banner ─────────────────────────────────────────────── */}
        {isSnapshotMode && (
          <div
            className="rounded-2xl px-5 py-4 flex items-center gap-4"
            style={{ background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.18)' }}
          >
            <div
              className="shrink-0 w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.22)' }}
            >
              <Database className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <div className="text-xs font-mono font-bold text-blue-400 tracking-wide">SNAPSHOT MODE — Market Closed</div>
              <div className="text-[10px] font-mono mt-0.5" style={{ color: 'rgba(96,165,250,0.55)' }}>
                Displaying last available EOD snapshot. Live data resumes at market open.
              </div>
            </div>
          </div>
        )}

        {/* ── Expiry selector ─────────────────────────────────────────────── */}
        {expiryList.length > 0 && (
          <div className="rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center gap-3" style={CARD}>
            <label
              className="text-[10px] font-mono font-bold tracking-widest uppercase whitespace-nowrap shrink-0"
              style={{ color: 'rgba(148,163,184,0.55)' }}
            >
              Expiry Date
            </label>
            <select
              value={selectedExpiry || ''}
              onChange={(e) => setSelectedExpiry(e.target.value)}
              className="flex-1 text-white text-sm font-mono px-3 py-2 rounded-xl outline-none transition-all cursor-pointer"
              style={{ background: 'rgba(0,0,0,0.35)', border: '1px solid rgba(0,229,255,0.15)', color: '#e2e8f0' }}
            >
              {expiryList.map((exp) => (
                <option key={exp} value={exp}>{exp}</option>
              ))}
            </select>
          </div>
        )}

        {/* ── Option Chain panel ─────────────────────────────────────────── */}
        <div id="section-chain" className="rounded-2xl overflow-hidden scroll-mt-20" style={CARD}>
          <div className="h-[1px] w-full" style={{ background: 'linear-gradient(90deg, transparent, rgba(99,102,241,0.5), transparent)' }} />
          <div className="p-4 sm:p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="text-[10px] font-bold tracking-[0.20em] uppercase mb-1" style={{ color: 'rgba(148,163,184,0.55)', fontFamily: "'JetBrains Mono', monospace" }}>
                Option Chain
              </div>
              {data?.optionChain && (
                <span className="text-[10px] font-mono" style={{ color: 'rgba(148,163,184,0.45)' }}>
                  {data.optionChain.calls?.length ?? 0}CE · {data.optionChain.puts?.length ?? 0}PE
                </span>
              )}
            </div>
            {data?.optionChain ? (
              <div className="text-xs font-mono" style={{ color: 'rgba(148,163,184,0.6)' }}>
                Option Chain Data Available — {data.optionChain.calls?.length ?? 0} calls, {data.optionChain.puts?.length ?? 0} puts
              </div>
            ) : (
              <div className="flex items-center justify-center py-6" style={{ color: 'rgba(148,163,184,0.3)' }}>
                <Activity className="w-5 h-5 mr-2" />
                <span className="text-xs font-mono">Awaiting data…</span>
              </div>
            )}
          </div>
        </div>

        {/* ── OI Heatmap ─────────────────────────────────────────────────── */}
        <div className="rounded-2xl overflow-hidden" style={CARD}>
          <div className="h-[1px] w-full" style={{ background: 'linear-gradient(90deg, transparent, rgba(245,158,11,0.40), transparent)' }} />
          <div className="p-4 sm:p-5">
            <MemoizedOIHeatmap symbol={symbol} />
          </div>
        </div>

        {/* ── AI Panel + Alerts ──────────────────────────────────────────── */}
        <div id="section-alerts" className="scroll-mt-20" />
        <DebugBadge className="mb-1" />
        <MemoizedAIPanel intelligence={data?.intelligence ?? null} />
        <MemoizedAlerts alerts={data?.alerts || []} />

      </div>
    </div>
  );
}
