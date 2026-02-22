"use client";

import React, { useState, useEffect, memo } from 'react';
import { WifiOff, TrendingUp, TrendingDown, Minus, Activity, AlertTriangle, Database, RefreshCw } from 'lucide-react';
import { useLiveMarketData } from '../hooks/useLiveMarketDataEnhanced';
import { useModeGuard, useEffectiveSpot, useSnapshotAnalytics, useTimeoutProtection } from '../components/SafeModeGuard';
import MarketStatusIndicator from './MarketStatusIndicator';
import DebugBadge from './DebugBadge';
import ProbabilityDisplay from './ProbabilityDisplay';
import ExpectedMoveChart from './ExpectedMoveChart';
import InstitutionalBias from './InstitutionalBias';
import SignalCards from './SignalCards';
import AIInterpretationPanel from './AIInterpretationPanel';

// ─── Shared Components ────────────────────────────────────────────────────────
import MarketMetrics from './MarketMetrics';
import BiasMeter from './BiasMeter';
import OIHeatmap from './OIHeatmap';

// ─── Structural Intelligence Panels ──────────────────────────────────────────
import StructuralBannerFinal from './intelligence/StructuralBannerFinal';
import GammaPressurePanelFinal from './intelligence/GammaPressurePanelFinal';
import SmartMoneyPanel from './intelligence/SmartMoneyPanel';
import ExpiryPanelFinal from './intelligence/ExpiryPanelFinal';
import AlertPanelFinal from './intelligence/AlertPanelFinal';

// ─── Memoized Components (Phase 4) ─────────────────────────────────────────────
const MemoizedMarketMetrics = memo(MarketMetrics);
const MemoizedInstitutionalBias = memo(InstitutionalBias);
const MemoizedSmartMoney = memo(SmartMoneyPanel);
const MemoizedGammaPressure = memo(GammaPressurePanelFinal);
const MemoizedOIHeatmap = memo(OIHeatmap);
const MemoizedAIPanel = memo(AIInterpretationPanel);
const MemoizedAlerts = memo(AlertPanelFinal);
const MemoizedExpectedMove = memo(ExpectedMoveChart);
const MemoizedBiasMeter = memo(BiasMeter);
const MemoizedProbability = memo(ProbabilityDisplay);

// ─── Helper Components ─────────────────────────────────────────────────────────

function LoadingBlock() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-300">
      <RefreshCw className="w-10 h-10 text-[#4F8CFF] animate-spin mb-4" />
      <p className="text-lg font-mono animate-pulse text-[#4F8CFF]/80 tracking-widest uppercase">Synchronizing Truth Agreement...</p>
    </div>
  );
}

function SnapshotReadyBlock() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[40vh] text-blue-300 bg-blue-950/20 rounded-2xl border border-blue-900/50 p-8 m-4">
      <Database className="w-12 h-12 text-blue-400 mb-4" />
      <h3 className="text-xl font-bold text-blue-400">Snapshot Mode Active</h3>
      <p className="mt-2 text-blue-300/70 text-center max-w-md">Using REST snapshot data - Market is currently closed</p>
    </div>
  );
}

function ErrorBlock({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[40vh] text-slate-300 bg-red-950/20 rounded-2xl border border-red-900/50 p-8 m-4">
      <WifiOff className="w-12 h-12 text-red-500 mb-4" />
      <h3 className="text-xl font-bold text-red-400">Connection Interrupted</h3>
      <p className="mt-2 text-red-300/70 text-center max-w-md">{message}</p>
    </div>
  );
}

// ─── Main Dashboard ────────────────────────────────────────────────────────────

export default function Dashboard() {
    console.log("🚀 ENHANCED DASHBOARD COMPONENT ACTIVE");
    const [symbol, setSymbol] = useState("NIFTY");
    const [expiryList, setExpiryList] = useState<string[]>([]);
    const [selectedExpiry, setSelectedExpiry] = useState<string | null>(null);

    // Use enhanced hook with market session support
    const { data, status, error, loading, mode } = useLiveMarketData(symbol, selectedExpiry);

    // Mode guards and analytics
    const isLiveMode = useModeGuard(mode, 'LIVE');
    const isSnapshotMode = useModeGuard(mode, 'SNAPSHOT');
    const isHaltedMode = useModeGuard(mode, 'HALTED');
    const effectiveSpot = useEffectiveSpot(data, mode);
    const snapshotAnalytics = useSnapshotAnalytics(mode, data?.data_source || '');
    const timeoutProtection = useTimeoutProtection(mode);
    
    // Analytics enabled guard
    const isAnalyticsEnabled = data?.analytics_enabled !== false;
    
    console.log("🔍 Dashboard Mode Analysis:", {
        mode,
        isLiveMode,
        isSnapshotMode,
        isHaltedMode,
        effectiveSpot,
        engineMode: status?.engine_mode,
        dataSource: data?.data_source,
        isAnalyticsEnabled
    });

    console.log("📦 Dashboard selectedExpiry:", selectedExpiry);
    console.log("📦 Dashboard data:", data);
    console.log("📦 Dashboard status:", status);
    console.log("Dashboard error:", error);

    const safeError = typeof error === "string" ? error : null;

    // ENGINE MODE UI VALIDATION GUARD
    React.useEffect(() => {
        if (mode !== "live") {
            console.log(`🛡️ ENGINE MODE GUARD: Disabling live animations - Mode: ${mode}`);
            // Disable live animations
            document.body.classList.add('snapshot-mode');
        } else {
            console.log("✅ ENGINE MODE GUARD: Enabling live animations");
            document.body.classList.remove('snapshot-mode');
        }
    }, [mode]);

    // Fetch expiries on mount
    useEffect(() => {
        const fetchExpiries = async () => {
            try {
                const res = await fetch(
                    `http://localhost:8000/api/v1/options/contract/${symbol}` 
                );
                
                if (!res.ok) {
                    throw new Error(`HTTP error! status: ${res.status}`);
                }
                
                const json = await res.json();

                if (json?.status === "success" && json?.data) {
                    // Handle both expiries array formats
                    const expiries = Array.isArray(json.data.expiries) ? json.data.expiries : json.data;
                    setExpiryList(expiries);
                    console.log("📅 Fetched expiries:", expiries);

                    if (expiries.length > 0) {
                        setSelectedExpiry(expiries[0]);
                        console.log("✅ Auto-selected expiry:", expiries[0]);
                    }
                } else {
                    // Fallback to hardcoded expiries if API fails
                    const fallbackExpiries = ["2026-02-24", "2026-03-02", "2026-03-10", "2026-03-17", "2026-03-24"];
                    setExpiryList(fallbackExpiries);
                    setSelectedExpiry(fallbackExpiries[0]);
                    console.log("📅 Using fallback expiries:", fallbackExpiries);
                }
            } catch (err) {
                console.error("Failed to fetch expiries", err);
                // Fallback to hardcoded expiries on error
                const fallbackExpiries = ["2026-02-24", "2026-03-02", "2026-03-10", "2026-03-17", "2026-03-24"];
                setExpiryList(fallbackExpiries);
                setSelectedExpiry(fallbackExpiries[0]);
                console.log("📅 Using fallback expiries due to error:", fallbackExpiries);
            }
        };

        fetchExpiries();
    }, [symbol]);

    // LOADING STATE FIX with snapshot mode support
    if (loading) {
        if (mode === 'snapshot') {
            return <SnapshotReadyBlock />;
        }
        return <LoadingBlock />;
    }

    if (safeError) {
        return <ErrorBlock message={safeError} />;
    }

    // TIMEOUT PROTECTION - Don't render live components in snapshot mode
    if (mode === 'snapshot' && !data) {
        return <SnapshotReadyBlock />;
    }

  return (
    <div className="bg-background text-text-primary min-h-screen">
      {/* MAIN CONTENT WRAPPER */}
      <div className="grid grid-cols-12 gap-3 p-3">
        
        {/* ROW 1 - TOP SPOT STRIP */}
        <div className="col-span-12 bg-card border border-border rounded-md p-3">
          <div className="grid grid-cols-12 gap-3 items-center">
            {/* Symbol Name */}
            <div className="col-span-3">
              <div className="text-sm font-mono font-bold text-text-primary">
                {symbol}
              </div>
            </div>
            
            {/* Spot Price */}
            <div className="col-span-3">
              <div className="text-lg font-mono font-bold text-text-primary">
                {effectiveSpot?.toFixed(2) || '0.00'}
                {mode === 'snapshot' && (
                  <span className="text-xs text-blue-400 ml-2">(REST)</span>
                )}
              </div>
            </div>
            
            {/* Price Change */}
            <div className="col-span-2">
              <div className={`text-sm font-mono font-bold ${data?.change >= 0 ? 'text-bullish' : 'text-bearish'}`}>
                {data?.change >= 0 ? '+' : ''}{data?.change_percent?.toFixed(2)}%
              </div>
            </div>
            
            {/* Market Status */}
            <div className="col-span-2">
              <div className={`text-xs font-mono px-2 py-1 rounded border ${
                status?.market_status === 'OPEN' ? 'bg-green-500/20 text-green-400 border-green-500/40' :
                status?.market_status === 'PRE_OPEN' ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40' :
                status?.market_status === 'CLOSED' ? 'bg-red-500/20 text-red-400 border-red-500/40' :
                status?.market_status === 'HALTED' ? 'bg-red-600/20 text-red-500 border-red-600/40' :
                'bg-gray-500/20 text-gray-400 border-gray-500/40'
              }`}>
                {status?.market_status || 'UNKNOWN'}
              </div>
            </div>
            
            {/* Engine Mode Indicator */}
            <div className="col-span-2">
              <div className={`text-xs font-mono px-2 py-1 rounded border ${
                mode === 'live' ? 'bg-green-500/20 text-green-400 border-green-500/40' :
                mode === 'snapshot' ? 'bg-blue-500/20 text-blue-400 border-blue-500/40' :
                mode === 'halted' ? 'bg-red-600/20 text-red-500 border-red-600/40' :
                'bg-gray-500/20 text-gray-400 border-gray-500/40'
              }`}>
                {mode === 'live' ? 'LIVE' : 
                 mode === 'snapshot' ? 'SNAPSHOT' :
                 mode === 'halted' ? 'HALTED' : 'OFFLINE'}
              </div>
            </div>
          </div>
        </div>

        {/* ROW 2 - MARKET BIAS + EXPECTED MOVE */}
        <div className="col-span-4 bg-card border border-border rounded-md p-3">
          <div className="text-xs font-bold text-text-secondary mb-3">MARKET BIAS</div>
          <div className="space-y-2">
            {/* Signal Tag */}
            <div className="flex items-center gap-2">
              <div className={`text-xs font-bold px-2 py-1 rounded ${
                data?.intelligence?.bias?.label === 'BULLISH' ? 'bg-green-500/20 text-green-400' :
                data?.intelligence?.bias?.label === 'BEARISH' ? 'bg-red-500/20 text-red-400' :
                'bg-neutral-500/20 text-neutral-400'
              }`}>
                {data?.intelligence?.bias?.label || 'HOLD'}
              </div>
              <div className="text-xs text-text-secondary">
                Strength: {data?.intelligence?.bias?.score?.toFixed(1) || '0.0'}
              </div>
            </div>
            
            {/* Confidence Bar */}
            <div className="w-full bg-border rounded-full h-2">
              <div 
                className="h-full bg-analytics-500 rounded-full transition-all"
                style={{ width: `${Math.abs(data?.intelligence?.bias?.score || 0) * 10}%` }}
              />
            </div>
            
            {/* Additional Info */}
            <div className="text-xs text-text-secondary">
              <div>Confidence: {Math.abs(data?.intelligence?.bias?.score || 0) > 0.7 ? 'HIGH' : Math.abs(data?.intelligence?.bias?.score || 0) > 0.4 ? 'MEDIUM' : 'LOW'}</div>
              <div>Pressure: {data?.intelligence?.bias?.label === 'BULLISH' ? 'BUYING' : data?.intelligence?.bias?.label === 'BEARISH' ? 'SELLING' : 'BALANCED'}</div>
            </div>
          </div>
        </div>

        <div className="col-span-8 bg-card border border-border rounded-md p-3">
          <div className="text-xs font-bold text-text-secondary mb-3">
            EXPECTED MOVE
            {isSnapshotMode && (
              <span className="text-xs text-blue-400 ml-2">(REST Premiums)</span>
            )}
          </div>
          <div className="space-y-3">
            {/* Range Bar */}
            <div className="flex items-center gap-3">
              <div className="text-sm font-mono text-bearish">
                {(data?.spot - (data?.intelligence?.probability?.expected_move || 0)).toFixed(2)}
              </div>
              <div className="flex-1 bg-border rounded-full h-3 relative">
                <div className="absolute inset-y-0 left-1/2 w-0.5 bg-text-primary"></div>
                <div className="absolute inset-y-0 left-0 right-0 flex items-center px-1">
                  <div className="w-full bg-analytics-500/20 rounded-full h-1"></div>
                </div>
              </div>
              <div className="text-sm font-mono text-bullish">
                {(data?.spot + (data?.intelligence?.probability?.expected_move || 0)).toFixed(2)}
              </div>
            </div>
            
            {/* Bounds */}
            <div className="flex justify-between text-xs text-text-secondary">
              <div>Lower: {(data?.spot - (data?.intelligence?.probability?.expected_move || 0)).toFixed(2)}</div>
              <div>Spot: {data?.spot?.toFixed(2)}</div>
              <div>Upper: {(data?.spot + (data?.intelligence?.probability?.expected_move || 0)).toFixed(2)}</div>
            </div>
            
            {/* Risk Badge */}
            <div className="text-xs font-mono px-2 py-1 bg-orange-500/20 text-orange-400 border border-orange-500/40 rounded">
              BREAKOUT RISK: {data?.intelligence?.probability?.breach_probability?.toFixed(0) || '0'}%
            </div>
          </div>
        </div>

        {/* ROW 3 - PCR + SMART MONEY + LIQUIDITY */}
        <div className="col-span-4 bg-card border border-border rounded-md p-3">
          <div className="text-xs font-bold text-text-secondary mb-3">EXPECTED MOVE</div>
          <div className="space-y-2">
            <div className="text-2xl font-mono font-bold text-text-primary">
              {data?.intelligence?.analytics_enabled ? 
                (data?.intelligence?.probability?.expected_move || 0).toFixed(2) :
                <span className="text-text-secondary">Waiting for valid market data...</span>
              }
            </div>
            <div className="text-xs text-text-secondary">
              {data?.intelligence?.analytics_enabled ? 
                `±${(data?.intelligence?.probability?.upper_1sd || 0).toFixed(2)}` :
                <span className="text-text-secondary">Std Dev unavailable</span>
              }
            </div>
            <div className="text-xs text-text-secondary">
              {data?.intelligence?.analytics_enabled ? 
                `${((data?.intelligence?.probability?.breach_probability || 0) * 100).toFixed(1)}% chance of breakout` :
                <span className="text-text-secondary">Breakout analysis unavailable</span>
              }
            </div>
            {!data?.intelligence?.analytics_enabled && (
              <div className="text-xs text-yellow-400 font-medium text-center p-2 rounded">
                ⚠️ Analytics Disabled - Engine calculations unavailable
              </div>
            )}
          </div>
        </div>

        <div className="col-span-4 bg-card border border-border rounded-md p-3">
          <div className="text-xs font-bold text-text-secondary mb-3">PUT-CALL RATIO</div>
          <div className="space-y-2">
            <div className="text-2xl font-mono font-bold text-text-primary">
              {data?.analytics?.pcr?.toFixed(2) || '0.00'}
            </div>
            <div className={`text-sm font-bold ${data?.analytics?.pcr > 1 ? 'text-bullish' : data?.analytics?.pcr < 1 ? 'text-bearish' : 'text-neutral'}`}>
              {data?.analytics?.pcr > 1 ? 'BULLISH BIAS' : data?.analytics?.pcr < 1 ? 'BEARISH BIAS' : 'NEUTRAL'}
            </div>
            <div className="text-xs text-text-secondary">
              Total CE OI: {(data?.analytics?.total_call_oi || 0).toLocaleString()}
            </div>
            <div className="text-xs text-text-secondary">
              Total PE OI: {(data?.analytics?.total_put_oi || 0).toLocaleString()}
            </div>
          </div>
        </div>

        <div className="col-span-4 bg-card border border-border rounded-md p-3">
          <div className="text-xs font-bold text-text-secondary mb-3">
            SMART MONEY
            {isSnapshotMode && (
              <span className="text-xs text-blue-400 ml-2">(DISABLED)</span>
            )}
          </div>
          <div className="space-y-2">
            {isLiveMode ? (
              <MemoizedSmartMoney smartMoneyData={data?.smart_money_activity ?? null} />
            ) : (
              <div className="text-xs text-text-secondary text-center py-4">
                Smart Money analysis disabled in {mode.toUpperCase()} mode
              </div>
            )}
          </div>
        </div>

        <div className="col-span-4 bg-card border border-border rounded-md p-3">
          <div className="text-xs font-bold text-text-secondary mb-3">LIQUIDITY</div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-text-secondary">Total OI</span>
              <span className="text-sm font-mono text-text-primary">
                {((data?.analytics?.total_call_oi || 0) + (data?.analytics?.total_put_oi || 0)).toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-text-secondary">OI Change</span>
              <span className="text-sm font-mono text-text-primary">
                {data?.analytics?.oi_change_24h?.toFixed(0) || '0'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-text-secondary">Volume</span>
              <span className="text-sm font-mono text-text-primary">
                {(data?.analytics?.total_volume || 0).toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-text-secondary">VWAP</span>
              <span className="text-sm font-mono text-text-primary">
                {data?.analytics?.vwap?.toFixed(2) || '0.00'}
              </span>
            </div>
          </div>
        </div>

        {/* ROW 4 - OPTION CHAIN (ALWAYS AT BOTTOM) */}
        <div className="col-span-12 bg-card border border-border rounded-md p-3">
          <div className="text-xs font-bold text-text-secondary mb-3">OPTION CHAIN</div>
          {data?.optionChain && (
            <div className="text-xs text-text-secondary">
              Option Chain Data Available: {data.optionChain.calls?.length || 0} calls, {data.optionChain.puts?.length || 0} puts
            </div>
          )}
        </div>

        {/* ADDITIONAL COMPONENTS */}
        <DebugBadge className="col-span-12 mb-3" />
        <MemoizedAIPanel intelligence={data?.intelligence ?? null} />
        <MemoizedAlerts alerts={data?.alerts || []} />
        <MemoizedOIHeatmap symbol={symbol} liveData={data?.optionChain ?? null} />

        {/* SNAPSHOT MODE LABEL */}
        {isSnapshotMode && (
          <div className="col-span-12 bg-blue-500/10 border border-blue-500/30 rounded-md p-3 mb-3">
            <div className="flex items-center gap-2 text-blue-400">
              <Database className="w-4 h-4" />
              <span className="text-sm font-mono font-bold">Snapshot Mode (Market Closed)</span>
            </div>
          </div>
        )}

        {/* EXPIRY SELECTOR */}
        {expiryList.length > 0 && (
          <div className="col-span-12 bg-card border border-border rounded-md p-3">
            <label className="text-sm text-text-secondary block mb-2">
              Select Expiry
            </label>
            <select
              value={selectedExpiry || ""}
              onChange={(e) => setSelectedExpiry(e.target.value)}
              className="bg-background border border-border text-text-primary px-3 py-2 rounded-md w-full"
            >
              {expiryList.map((exp) => (
                <option key={exp} value={exp}>
                  {exp}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
    </div>
  );
}
