"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Wifi, WifiOff, Heart, BarChart2, Link2, Activity, Bell } from 'lucide-react';
import { useWSStore } from '../../core/ws/wsStore';
import { WS_BACKEND_ONLINE_EVENT } from '../../hooks/useLiveMarketData';
import api from '../../api/axios';

// ── How often Navbar independently pings the backend (ms) ───────────────────
const NAVBAR_HEALTH_POLL_MS = 5_000; // 5s — fast enough to feel instant

// ── Keyframes ────────────────────────────────────────────────────────────────
const HEARTBEAT_CSS = `
@keyframes ws-heartbeat {
  0%   { transform: scale(1);    }
  10%  { transform: scale(1.40); }
  20%  { transform: scale(1);    }
  30%  { transform: scale(1.28); }
  40%  { transform: scale(1);    }
  100% { transform: scale(1);    }
}
@keyframes ws-glow-pulse {
  0%, 100% { box-shadow: 0 0 6px 1px rgba(34,197,94,0.28); }
  30%       { box-shadow: 0 0 16px 5px rgba(34,197,94,0.55); }
}
@keyframes ecg-scan {
  0%   { stroke-dashoffset: 120; opacity: 0; }
  10%  { opacity: 1; }
  80%  { opacity: 1; }
  100% { stroke-dashoffset: 0;   opacity: 0; }
}
@keyframes flatline-blink {
  0%, 100% { opacity: 0.22; }
  50%       { opacity: 0.50; }
}
`;

// Nav tab definitions — id matches the section IDs in Dashboard.tsx
const NAV_TABS = [
  { id: 'dashboard', sectionId: 'section-dashboard', label: 'Dashboard', icon: BarChart2 },
  { id: 'chain', sectionId: 'section-chain', label: 'Options Chain', icon: Link2 },
  { id: 'analytics', sectionId: 'section-analytics', label: 'Analytics', icon: Activity },
  { id: 'alerts', sectionId: 'section-alerts', label: 'Alerts', icon: Bell },
] as const;

type TabId = typeof NAV_TABS[number]['id'];

function scrollToSection(sectionId: string) {
  const el = document.getElementById(sectionId);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

export default function Navbar() {
  // ── WS state from shared store (Dashboard populates this) ──────────────────
  const isConnected = useWSStore((state) => state.isConnected);


  // ── Independent backend health probe ───────────────────────────────────────
  // This runs in the Navbar itself so the heart ALWAYS reflects server state,
  // even after useLiveOptionsWS gives up on reconnects.
  const prevAliveRef = useRef<boolean | null>(null);

  useEffect(() => {
    const probe = async () => {
      let alive = false;
      try {
        const res = await fetch('/api/v1/market/session', {
          method: 'GET', credentials: 'include',
          signal: AbortSignal.timeout(4_000),
        });
        // 2xx = backend is truly alive
        // 502/503 = Next.js proxy error (backend down) — must NOT count as alive
        alive = res.ok;
      } catch {
        alive = false;
      }

      // Fire the reconnect event ONLY on the false → true transition
      if (alive && prevAliveRef.current === false) {
        console.log('📡 Navbar: backend online — firing WS reconnect event');
        window.dispatchEvent(new CustomEvent(WS_BACKEND_ONLINE_EVENT));
      }
      prevAliveRef.current = alive;
    };

    probe();
    const id = setInterval(probe, NAVBAR_HEALTH_POLL_MS);
    return () => clearInterval(id);
  }, []);

  // ── Heart: simple 2-state — green = WS connected, red = disconnected ──────────
  const wsGreen = isConnected;

  const [marketStatus, setMarketStatus] = useState<string>('UNKNOWN');
  const [activeTab, setActiveTab] = useState<TabId>('dashboard');

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await api.get('/api/v1/market/session');
        const result = response.data;
        if (result?.status === 'success' && result?.data?.market_status) {
          setMarketStatus(result.data.market_status);
        } else if (result?.market_status) {
          setMarketStatus(result.market_status);
        }
      } catch {
        console.warn('Navbar: failed to fetch market status');
      }
    };
    fetchStatus();
    const id = setInterval(fetchStatus, 60_000);
    return () => clearInterval(id);
  }, []);

  // Track active section on scroll
  useEffect(() => {
    const handleScroll = () => {
      const offsets = NAV_TABS.map((tab) => {
        const el = document.getElementById(tab.sectionId);
        if (!el) return { id: tab.id, top: Infinity };
        return { id: tab.id, top: Math.abs(el.getBoundingClientRect().top - 80) };
      });
      const closest = offsets.reduce((a, b) => (a.top < b.top ? a : b));
      setActiveTab(closest.id as TabId);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const OPEN_STATES = ['OPEN', 'PRE_OPEN', 'OPENING_END'];
  const marketOpen = OPEN_STATES.includes(marketStatus);

  const handleTabClick = (tab: typeof NAV_TABS[number]) => {
    setActiveTab(tab.id);
    scrollToSection(tab.sectionId);
  };

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: HEARTBEAT_CSS }} />

      {/* ════════════════════════════════════════════════════════════
          TOP NAVBAR
      ════════════════════════════════════════════════════════════ */}
      <nav className="sticky top-0 z-50 w-full">

        {/* Top neon accent line */}
        <div
          className="h-[2px] w-full"
          style={{
            background: 'linear-gradient(90deg, transparent 0%, #00E5FF 30%, #7C3AED 70%, transparent 100%)',
          }}
        />

        {/* Glass bar */}
        <div
          className="border-b backdrop-blur-2xl"
          style={{
            background: 'rgba(10, 13, 28, 0.92)',
            borderColor: 'rgba(255,255,255,0.05)',
          }}
        >
          <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-10">
            <div className="h-14 sm:h-[60px] flex items-center justify-between gap-3">

              {/* ── LEFT: Logo ─────────────────────────────────────────── */}
              <div className="flex items-center gap-2.5 shrink-0">
                <div
                  className="flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-xl shrink-0"
                  style={{
                    background: 'linear-gradient(135deg, rgba(0,229,255,0.20) 0%, rgba(124,58,237,0.14) 100%)',
                    border: '1px solid rgba(0,229,255,0.22)',
                    boxShadow: '0 0 18px rgba(0,229,255,0.14)',
                  }}
                >
                  <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
                    <path d="M2 12L6 6L9 9L13 3" stroke="#00E5FF" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    <circle cx="13" cy="3" r="1.5" fill="#00E5FF" />
                    <path d="M2 14H14" stroke="#7C3AED" strokeWidth="1" strokeLinecap="round" opacity="0.6" />
                  </svg>
                </div>
                <div className="leading-none select-none">
                  <div
                    className="text-[17px] sm:text-[19px] font-black tracking-tight"
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
                    className="text-[8px] sm:text-[9px] tracking-[0.22em] uppercase font-semibold mt-0.5 hidden sm:block"
                    style={{ color: 'rgba(129,140,248,0.65)', fontFamily: "'JetBrains Mono', monospace" }}
                  >
                    Options Intelligence
                  </div>
                </div>
              </div>

              {/* ── CENTER: Nav tabs — desktop md+ ─────────────────────── */}
              <div
                className="hidden md:flex items-center gap-0.5 p-1 rounded-xl"
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}
              >
                {NAV_TABS.map((tab) => {
                  const isActive = activeTab === tab.id;
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => handleTabClick(tab)}
                      className="relative flex items-center gap-1.5 px-3 lg:px-4 py-1.5 rounded-lg text-[11px] lg:text-xs font-semibold transition-all duration-200 focus:outline-none"
                      style={
                        isActive
                          ? {
                            background: 'linear-gradient(135deg, rgba(0,229,255,0.16) 0%, rgba(124,58,237,0.12) 100%)',
                            border: '1px solid rgba(0,229,255,0.22)',
                            color: '#00E5FF',
                            boxShadow: '0 0 12px rgba(0,229,255,0.14)',
                            fontFamily: "'Space Grotesk', sans-serif",
                          }
                          : {
                            background: 'transparent',
                            border: '1px solid transparent',
                            color: 'rgba(148,163,184,0.65)',
                            fontFamily: "'Space Grotesk', sans-serif",
                          }
                      }
                    >
                      <Icon
                        style={{
                          width: '12px',
                          height: '12px',
                          flexShrink: 0,
                          color: isActive ? '#00E5FF' : 'rgba(148,163,184,0.45)',
                        }}
                      />
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </div>

              {/* ── RIGHT: Status + WS Heart ─────────────────────────── */}
              <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">

                {/* Market status — sm+ */}
                <div
                  className="hidden sm:flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-full text-[10px] sm:text-[11px] font-bold font-mono select-none"
                  style={
                    marketOpen
                      ? {
                        background: 'rgba(34,197,94,0.10)',
                        border: '1px solid rgba(34,197,94,0.28)',
                        color: '#4ade80',
                        boxShadow: '0 0 10px rgba(34,197,94,0.12)',
                      }
                      : {
                        background: 'rgba(239,68,68,0.07)',
                        border: '1px solid rgba(239,68,68,0.20)',
                        color: '#f87171',
                      }
                  }
                >
                  {marketOpen
                    ? <Wifi style={{ width: 11, height: 11, flexShrink: 0 }} />
                    : <WifiOff style={{ width: 11, height: 11, flexShrink: 0 }} />
                  }
                  <span className="hidden lg:inline">{marketOpen ? 'MARKET OPEN' : 'MARKET CLOSED'}</span>
                  <span className="lg:hidden">{marketOpen ? 'OPEN' : 'CLOSED'}</span>
                </div>


                {/* WS Heartbeat — green = connected, red = offline */}
                <div
                  className="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-2.5 py-1.5 rounded-xl border select-none shrink-0 transition-all duration-500"
                  title={wsGreen ? 'WebSocket: Connected' : 'WebSocket: Disconnected'}
                  style={
                    wsGreen
                      ? {
                        background: 'rgba(34,197,94,0.07)',
                        border: '1px solid rgba(34,197,94,0.25)',
                        animation: 'ws-glow-pulse 0.85s ease-in-out infinite',
                      }
                      : {
                        background: 'rgba(239,68,68,0.06)',
                        border: '1px solid rgba(239,68,68,0.18)',
                      }
                  }
                >
                  <Heart
                    style={{
                      width: 13, height: 13, flexShrink: 0,
                      color: wsGreen ? '#4ade80' : '#f87171',
                      fill: wsGreen ? 'rgba(34,197,94,0.50)' : 'rgba(239,68,68,0.32)',
                      animation: wsGreen ? 'ws-heartbeat 0.85s ease-in-out infinite' : 'none',
                      transformOrigin: 'center',
                      willChange: 'transform',
                    }}
                  />
                  {/* ECG line — sm+ */}
                  <div className="hidden sm:block" style={{ width: 34, height: 15, overflow: 'hidden' }}>
                    <svg viewBox="0 0 120 36" width="34" height="15" preserveAspectRatio="none" style={{ display: 'block' }}>
                      {wsGreen ? (
                        <path
                          d="M0,18 L28,18 L38,18 L46,4 L53,32 L60,18 L68,18 L75,10 L81,26 L87,18 L120,18"
                          fill="none" stroke="#4ade80" strokeWidth="2.4"
                          strokeLinecap="round" strokeLinejoin="round" strokeDasharray="120"
                          style={{ animation: 'ecg-scan 1.7s ease-in-out infinite', filter: 'drop-shadow(0 0 3px rgba(34,197,94,0.9))' }}
                        />
                      ) : (
                        <path d="M0,18 L120,18" fill="none" stroke="#f87171" strokeWidth="1.5"
                          strokeLinecap="round" style={{ animation: 'flatline-blink 2s ease-in-out infinite' }} />
                      )}
                    </svg>
                  </div>
                  <span
                    className="hidden sm:inline text-[10px] font-bold"
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      color: wsGreen ? '#86efac' : '#fca5a5',
                      letterSpacing: '0.07em',
                    }}
                  >
                    WS
                  </span>
                </div>

              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* ════════════════════════════════════════════════════════════
          MOBILE BOTTOM NAV BAR — visible only on < md
      ════════════════════════════════════════════════════════════ */}
      <div
        className="md:hidden fixed bottom-0 left-0 right-0 z-50"
        style={{
          background: 'rgba(10,13,28,0.96)',
          borderTop: '1px solid rgba(255,255,255,0.07)',
          backdropFilter: 'blur(20px)',
          paddingBottom: 'env(safe-area-inset-bottom)',
        }}
      >
        <div className="flex items-center justify-around px-2 py-2">
          {NAV_TABS.map((tab) => {
            const isActive = activeTab === tab.id;
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabClick(tab)}
                className="flex flex-col items-center gap-1 px-3 py-1.5 rounded-xl transition-all duration-200 min-w-[60px] focus:outline-none"
                style={{
                  background: isActive ? 'rgba(0,229,255,0.08)' : 'transparent',
                  border: isActive ? '1px solid rgba(0,229,255,0.18)' : '1px solid transparent',
                }}
              >
                <Icon
                  style={{
                    width: 18, height: 18,
                    color: isActive ? '#00E5FF' : 'rgba(148,163,184,0.40)',
                    filter: isActive ? 'drop-shadow(0 0 4px rgba(0,229,255,0.6))' : 'none',
                    transition: 'all 0.2s',
                  }}
                />
                <span
                  className="text-[9px] font-semibold leading-none"
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    color: isActive ? '#00E5FF' : 'rgba(148,163,184,0.35)',
                    letterSpacing: '0.04em',
                  }}
                >
                  {tab.id === 'chain' ? 'Chain' : tab.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </>
  );
}
