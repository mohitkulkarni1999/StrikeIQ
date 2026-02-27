import React, { useState, useEffect, useRef } from 'react';
import { Clock, Wifi, WifiOff, ServerOff } from 'lucide-react';
import api from '../api/axios';

interface MarketSession {
  market_status: 'OPEN' | 'CLOSED' | 'PRE_OPEN' | 'OPENING_END' | 'CLOSING' | 'CLOSING_END' | 'HALTED' | 'UNKNOWN';
  engine_mode: 'LIVE' | 'SNAPSHOT' | 'HALTED' | 'OFFLINE';
  last_check?: string;
  is_polling?: boolean;
}

interface MarketStatusIndicatorProps {
  className?: string;
}

const MarketStatusIndicator: React.FC<MarketStatusIndicatorProps> = ({ className = "" }) => {
  const [session, setSession] = useState<MarketSession>({
    market_status: 'UNKNOWN',
    engine_mode: 'OFFLINE',
  });
  const [loading, setLoading] = useState(true);
  // 'ok' | 'offline' — never show a hard error badge, just go silent/offline
  const [backendState, setBackendState] = useState<'ok' | 'offline'>('ok');
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Allow inner function to reference itself for scheduling retries
  const fetchRef = useRef<() => Promise<void>>();

  const scheduleNext = (delayMs: number) => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(() => fetchRef.current?.(), delayMs);
  };

  const fetchMarketStatus = async () => {
    try {
      const response = await api.get('/api/v1/market/session');
      const result = response.data;

      if (result?.status === 'success' && result?.data) {
        setSession(result.data);
      } else if (result?.market_status) {
        // Flat response shape fallback
        setSession({
          market_status: result.market_status,
          engine_mode: result.engine_mode ?? 'OFFLINE',
        });
      }
      setBackendState('ok');
      scheduleNext(10_000); // Normal cadence when backend healthy
    } catch {
      // Backend down / 500 / network error
      // ✅ Use warn not error — it's expected when backend is intentionally offline
      console.warn('[MarketStatusIndicator] Backend unreachable — retrying in 60s');
      setBackendState('offline');
      scheduleNext(60_000); // Back off on failure; don't hammer a dead server
    } finally {
      setLoading(false);
    }
  };

  fetchRef.current = fetchMarketStatus;

  useEffect(() => {
    fetchMarketStatus();
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Loading — first fetch not done yet ──────────────────────────────────
  if (loading) {
    return (
      <div
        className={`flex items-center gap-2 px-2.5 py-1 rounded-lg border ${className}`}
        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}
      >
        <div className="w-2.5 h-2.5 border border-slate-600 border-t-slate-400 rounded-full animate-spin" />
        <span className="text-[10px] text-slate-600 font-mono">...</span>
      </div>
    );
  }

  // ── Backend is down — show quiet, non-alarming offline badge ────────────
  if (backendState === 'offline') {
    return (
      <div
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border select-none ${className}`}
        title="Backend server is offline or unreachable"
        style={{
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.07)',
        }}
      >
        <ServerOff className="w-3 h-3" style={{ color: '#4B5563' }} />
        <span
          className="text-[10px] font-mono"
          style={{ color: '#4B5563', letterSpacing: '0.06em' }}
        >
          OFFLINE
        </span>
      </div>
    );
  }

  // ── Backend healthy — show real market status ────────────────────────────
  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'OPEN': return { bg: 'rgba(34,197,94,0.10)', border: 'rgba(34,197,94,0.30)', color: '#4ade80' };
      case 'PRE_OPEN': return { bg: 'rgba(234,179,8,0.10)', border: 'rgba(234,179,8,0.30)', color: '#facc15' };
      case 'OPENING_END': return { bg: 'rgba(249,115,22,0.10)', border: 'rgba(249,115,22,0.30)', color: '#fb923c' };
      case 'CLOSING': return { bg: 'rgba(168,85,247,0.10)', border: 'rgba(168,85,247,0.30)', color: '#c084fc' };
      case 'CLOSING_END': return { bg: 'rgba(99,102,241,0.10)', border: 'rgba(99,102,241,0.30)', color: '#818cf8' };
      case 'CLOSED': return { bg: 'rgba(239,68,68,0.07)', border: 'rgba(239,68,68,0.22)', color: '#f87171' };
      case 'HALTED': return { bg: 'rgba(239,68,68,0.12)', border: 'rgba(239,68,68,0.30)', color: '#ef4444' };
      default: return { bg: 'rgba(255,255,255,0.03)', border: 'rgba(255,255,255,0.07)', color: '#6B7280' };
    }
  };

  const getModeIcon = (mode: string) => {
    switch (mode) {
      case 'LIVE': return <Wifi className="w-3 h-3" />;
      case 'SNAPSHOT': return <Clock className="w-3 h-3" />;
      default: return <WifiOff className="w-3 h-3" />;
    }
  };

  const getModeColor = (mode: string) => {
    switch (mode) {
      case 'LIVE': return '#4ade80';
      case 'SNAPSHOT': return '#60a5fa';
      default: return '#6B7280';
    }
  };

  const statusStyle = getStatusStyle(session.market_status);

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Market Status pill */}
      <div
        className="flex items-center px-2.5 py-1 rounded-lg border text-[10px] font-bold font-mono select-none"
        style={{
          background: statusStyle.bg,
          border: `1px solid ${statusStyle.border}`,
          color: statusStyle.color,
          letterSpacing: '0.06em',
        }}
      >
        {session.market_status}
      </div>

      {/* Engine Mode */}
      <div
        className="flex items-center gap-1 text-[10px] font-mono"
        style={{ color: getModeColor(session.engine_mode) }}
      >
        {getModeIcon(session.engine_mode)}
        <span className="hidden sm:inline">{session.engine_mode}</span>
      </div>
    </div>
  );
};

export default MarketStatusIndicator;
