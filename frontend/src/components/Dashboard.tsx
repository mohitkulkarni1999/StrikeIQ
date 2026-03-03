"use client";

import React, { useState, useEffect, memo } from 'react';
import { Activity, Database } from 'lucide-react';
import { useLiveMarketData } from '../hooks/useLiveMarketData';
import { useExpirySelector } from '../hooks/useExpirySelector';
import { useMarketStore } from '../stores/marketStore';
import { useModeGuard, useEffectiveSpot, useSnapshotAnalytics, useTimeoutProtection } from './SafeModeGuard';
import DebugBadge from './DebugBadge';
import SymbolSelector from './SymbolSelector';
import AIInterpretationPanel from './AIInterpretationPanel';
import AICommandCenter from './AICommandCenter';
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
const MemoizedAICommandCenter = memo(AICommandCenter);

// ── Types ─────────────────────────────────────────────────────────────────────
interface DashboardProps { initialSymbol?: string; }

export default function Dashboard({ initialSymbol = 'NIFTY' }: DashboardProps) {
  // Initialize store with initial symbol if needed
  const setCurrentSymbol = useMarketStore(state => state.setCurrentSymbol);
  const currentSymbol = useMarketStore(state => state.currentSymbol);
  
  useEffect(() => {
    // Only set initial symbol if store symbol is still default
    if (currentSymbol === 'NIFTY' && initialSymbol !== 'NIFTY') {
      setCurrentSymbol(initialSymbol);
    }
  }, [initialSymbol, setCurrentSymbol, currentSymbol]);

  // Use expiry selector hook - reads symbol from store automatically
  const {
    expiryList,
    selectedExpiry,
    loadingExpiries,
    expiryError,
    handleExpiryChange,
    optionChainConnected
  } = useExpirySelector();

  const { data, error, loading, mode } = useLiveMarketData(currentSymbol, selectedExpiry);
  
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

  // Add dashboard card styles
  React.useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      .trading-panel {
        background: rgba(255,255,255,0.04);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.08);
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
      }
      
      .trading-panel::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        opacity: 0;
        transition: opacity 0.3s ease;
      }
      
      .trading-panel:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        border-color: rgba(255,255,255,0.12);
      }
      
      .trading-panel:hover::before {
        opacity: 1;
      }
      
      .full-width {
        grid-column: 1 / -1;
      }
      
      .chip {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 20px;
        padding: 8px 16px;
        color: white;
        cursor: pointer;
        transition: all 0.2s ease;
        font-weight: 500;
      }
      
      .chip:hover {
        background: rgba(255,255,255,0.2);
        border-color: rgba(255,255,255,0.3);
      }
      
      .chip-active {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        border: 1px solid #3b82f6;
        border-radius: 20px;
        padding: 8px 16px;
        color: white;
        cursor: pointer;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
      }
      
      /* Typography System */
      .panel-title {
        font-size: 14px;
        font-weight: 600;
        color: white;
      }
      
      .panel-value {
        font-size: 18px;
        font-weight: 700;
        color: white;
      }
      
      @media (max-width: 768px) {
        .dashboard-grid {
          grid-template-columns: 1fr !important;
        }
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);

  const safeError = typeof error === 'string' ? error : null;
  const modeLabel = mode === 'live' ? 'LIVE' : mode === 'snapshot' ? 'SNAPSHOT' : mode === 'error' ? 'HALTED' : 'OFFLINE';
  const modeColor = mode === 'live' ? '#4ade80' : mode === 'snapshot' ? '#60a5fa' : '#f87171';

  // ── State guards ──────────────────────────────────────────────────────────
  if (loading) return mode === 'snapshot' ? <SnapshotReadyBlock /> : <LoadingBlock />;
  if (safeError) return <ErrorBlock message={safeError} />;
  // CRITICAL FIX: Always render UI, even in snapshot mode without data
  // Remove blocking condition that was preventing dashboard from rendering

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

      <div className="relative z-10 max-w-[1920px] mx-auto px-3 sm:px-5 lg:px-8 py-4 sm:py-6">
        <div className="dashboard-grid" style={{
          display: 'grid',
          gridTemplateColumns: '1fr',
          gap: '20px'
        }}>

        {/* ROW 1 — Symbol Selector + Ticker strip (full width) */}
        <div className="full-width" style={{ gridColumn: '1 / -1' }}>
          <div className="trading-panel mb-4">
            <SymbolSelector />
          </div>
          <div className="trading-panel">
            <TickerStrip
              symbol={currentSymbol}
              data={data}
              effectiveSpot={effectiveSpot}
              mode={mode}
              modeLabel={modeLabel}
              modeColor={modeColor}
            />
          </div>
        </div>

        {/* ROW 2 — Four stat cards (full width) */}
        <div className="full-width" style={{ gridColumn: '1 / -1' }}>
          <div className="trading-panel">
            <StatCardsRow data={data} isAnalyticsEnabled={isAnalyticsEnabled} />
          </div>
        </div>

        {/* ROW 3 — Alert Panel (compact) */}
        <div className="full-width" style={{ gridColumn: '1 / -1' }}>
          <div className="trading-panel" style={{ minHeight: '120px' }}>
            <MemoizedAlerts alerts={(data as any)?.alerts || []} />
          </div>
        </div>

        {/* ROW 4 — Market Bias + Expected Move | Smart Money + Liquidity */}
        <div className="trading-panel">
          <BiasAndMove data={data} isSnapshotMode={isSnapshotMode} />
        </div>

        <div className="trading-panel">
          <SmartMoneyAndLiquidity
            data={data}
            isLiveMode={isLiveMode}
            isSnapshotMode={isSnapshotMode}
            mode={mode}
          />
        </div>

        {/* ROW 5 — OI Heatmap (full width horizontal scroll) */}
        <div className="full-width" style={{ gridColumn: '1 / -1' }}>
          <div className="trading-panel">
            <div id="oi-heatmap" className="rounded-2xl overflow-x-auto" style={CARD}>
              <div className="h-[1px] w-full" style={{ background: 'linear-gradient(90deg, transparent, rgba(245,158,11,0.40), transparent)' }} />
              <div className="p-4 sm:p-5 min-w-[800px]">
                <MemoizedOIHeatmap symbol={currentSymbol} />
              </div>
            </div>
          </div>
        </div>

        {/* ROW 7 — AI Interpretation Panel */}
        <div className="full-width" style={{ gridColumn: '1 / -1' }}>
          <div className="trading-panel">
            <div id="section-ai" className="scroll-mt-20" />
            <DebugBadge className="mb-1" />
            <MemoizedAIPanel intelligence={data?.intelligence ?? null} />
          </div>
        </div>

        {/* ROW 8 — AI Command Center */}
        <div className="full-width" style={{ gridColumn: '1 / -1' }}>
          <div className="trading-panel">
            <MemoizedAICommandCenter />
          </div>
        </div>

        </div>
      </div>
    </div>
  );
}
