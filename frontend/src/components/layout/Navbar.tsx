"use client";

import React, { useState, useEffect, useRef } from "react";
import { Wifi, WifiOff, Heart, BarChart2, Link2, Activity, Bell } from "lucide-react";
import { useWSStore } from "../../core/ws/wsStore";
import { WS_BACKEND_ONLINE_EVENT } from "../../hooks/useLiveMarketData";
import api from "../../api/axios";

const NAVBAR_HEALTH_POLL_MS = 10000;

const HEARTBEAT_CSS = `
@keyframes ws-heartbeat {
  0% { transform: scale(1); }
  10% { transform: scale(1.4); }
  20% { transform: scale(1); }
  30% { transform: scale(1.28); }
  40% { transform: scale(1); }
}

@keyframes ecg-scan {
  0% { stroke-dashoffset:120; opacity:0; }
  10% { opacity:1; }
  80% { opacity:1; }
  100% { stroke-dashoffset:0; opacity:0; }
}

@keyframes flatline-blink {
  0%,100% { opacity:0.25; }
  50% { opacity:0.5; }
}
`;

const NAV_TABS = [
  { id: "dashboard", sectionId: "section-dashboard", label: "Dashboard", icon: BarChart2 },
  { id: "chain", sectionId: "section-chain", label: "Options Chain", icon: Link2 },
  { id: "analytics", sectionId: "section-analytics", label: "Analytics", icon: Activity },
  { id: "alerts", sectionId: "section-alerts", label: "Alerts", icon: Bell },
] as const;

type TabId = typeof NAV_TABS[number]["id"];

function scrollToSection(sectionId: string) {
  const el = document.getElementById(sectionId);
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

export default function Navbar() {

  const connected = useWSStore((s) => s.connected);
  const marketStatus = useWSStore((s) => s.marketStatus);
  const wsStatus = useWSStore((s) => s.wsStatus);
  const setMarketStatus = useWSStore((s) => s.setMarketStatus);

  const [backendAlive, setBackendAlive] = useState(true);
  const prevAliveRef = useRef<boolean | null>(null);

  const [activeTab, setActiveTab] = useState<TabId>("dashboard");

  const OPEN_STATES = ["OPEN", "PRE_OPEN", "OPENING_END"];

  const marketColor =
    OPEN_STATES.includes(marketStatus)
      ? "bg-green-500"
      : marketStatus === "CLOSED"
      ? "bg-red-500"
      : "bg-gray-500";

  const wsGreen = backendAlive && connected;
  const wsRed = backendAlive && !connected;
  const wsGrey = !backendAlive;

  useEffect(() => {
    const probe = async () => {
      let alive = false;

      try {
        const res = await fetch("/api/v1/market/session", {
          method: "GET",
          credentials: "include",
        });

        alive = res.ok;
      } catch {
        alive = false;
      }

      setBackendAlive(alive);

      if (alive && prevAliveRef.current === false) {
        window.dispatchEvent(new CustomEvent(WS_BACKEND_ONLINE_EVENT));
      }

      prevAliveRef.current = alive;
    };

    probe();

    const id = setInterval(probe, NAVBAR_HEALTH_POLL_MS);

    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await api.get("/api/v1/market/session");
        const result = response.data;

        if (result?.status === "success" && result?.data?.market_status) {
          setMarketStatus(result.data.market_status);
        } else if (result?.market_status) {
          setMarketStatus(result.market_status);
        }
      } catch {
        console.warn("Navbar: failed to fetch market status");
      }
    };

    fetchStatus();
    const id = setInterval(fetchStatus, 60000);
    return () => clearInterval(id);
  }, []);

  const handleTabClick = (tab: typeof NAV_TABS[number]) => {
    setActiveTab(tab.id);
    scrollToSection(tab.sectionId);
  };

  const marketOpen = OPEN_STATES.includes(marketStatus);

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: HEARTBEAT_CSS }} />

      <nav className="sticky top-0 z-50 w-full bg-[#0a0d1c] border-b border-white/5 backdrop-blur-xl">
        <div className="max-w-[1920px] mx-auto px-6">
          <div className="h-[60px] flex items-center justify-between">

            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 flex items-center justify-center rounded-xl border border-cyan-400/30 bg-cyan-400/10">
                <svg width="16" height="16" viewBox="0 0 16 16">
                  <path d="M2 12L6 6L9 9L13 3" stroke="#00E5FF" strokeWidth="2" strokeLinecap="round"/>
                  <circle cx="13" cy="3" r="1.5" fill="#00E5FF"/>
                </svg>
              </div>

              <div>
                <div className="text-lg font-bold text-cyan-400">StrikeIQ</div>
                <div className="text-[10px] text-indigo-300/70 uppercase tracking-widest">
                  Options Intelligence
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="hidden md:flex items-center gap-2 bg-white/5 border border-white/10 p-1 rounded-xl">

              {NAV_TABS.map((tab) => {
                const Icon = tab.icon;
                const active = activeTab === tab.id;

                return (
                  <button
                    key={tab.id}
                    onClick={() => handleTabClick(tab)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition ${
                      active
                        ? "bg-cyan-500/20 border border-cyan-400/30 text-cyan-400"
                        : "text-slate-400"
                    }`}
                  >
                    <Icon size={14} />
                    {tab.label}
                  </button>
                );
              })}

            </div>

            {/* Status */}
            <div className="flex items-center gap-3">

              {/* Market */}
              <div className={`px-3 py-1 rounded-full text-xs font-bold text-white ${marketColor}`}>
                {marketOpen ? (
                  <span className="flex items-center gap-1">
                    <Wifi size={12} /> OPEN
                  </span>
                ) : (
                  <span className="flex items-center gap-1">
                    <WifiOff size={12} /> CLOSED
                  </span>
                )}
              </div>

              {/* WebSocket Heart */}
              <div
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border"
                style={
                  wsGreen
                    ? { background: "rgba(34,197,94,0.07)", border: "1px solid rgba(34,197,94,0.25)" }
                    : wsRed
                    ? { background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.18)" }
                    : { background: "rgba(156,163,175,0.06)", border: "1px solid rgba(156,163,175,0.18)" }
                }
              >
                <Heart
                  style={{
                    width: 13,
                    height: 13,
                    flexShrink: 0,
                    color: wsGreen ? "#4ade80" : wsRed ? "#f87171" : "#9ca3af",
                    fill: wsGreen
                      ? "rgba(34,197,94,0.50)"
                      : wsRed
                      ? "rgba(239,68,68,0.32)"
                      : "rgba(148,163,184,0.25)",
                    animation: wsGreen ? "ws-heartbeat 0.85s ease-in-out infinite" : "none",
                    transformOrigin: "center",
                  }}
                />

                {/* ECG Graph */}
                <div className="hidden sm:block" style={{ width: 34, height: 15, overflow: "hidden" }}>
                  <svg viewBox="0 0 120 36" width="34" height="15">
                    {wsGreen ? (
                      <path
                        d="M0,18 L28,18 L38,18 L46,4 L53,32 L60,18 L68,18 L75,10 L81,26 L87,18 L120,18"
                        fill="none"
                        stroke="#4ade80"
                        strokeWidth="2.4"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeDasharray="120"
                        style={{
                          animation: "ecg-scan 1.7s ease-in-out infinite",
                          filter: "drop-shadow(0 0 3px rgba(34,197,94,0.9))",
                        }}
                      />
                    ) : (
                      <path
                        d="M0,18 L120,18"
                        fill="none"
                        stroke={wsRed ? "#f87171" : "#9ca3af"}
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        style={{ animation: "flatline-blink 2s ease-in-out infinite" }}
                      />
                    )}
                  </svg>
                </div>

                <span className="hidden sm:inline text-[10px] font-bold text-slate-300">
                  WS
                </span>

              </div>

            </div>

          </div>
        </div>
      </nav>
    </>
  );
}