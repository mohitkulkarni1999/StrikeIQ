"use client";

import React, { useState } from 'react';
import { Wifi, WifiOff, Activity, ChevronDown } from 'lucide-react';
import { useLiveMarketData } from '../../hooks/useLiveMarketData';
import MarketStatusIndicator from '../MarketStatusIndicator';

export default function Navbar() {
  const [symbol, setSymbol] = useState("NIFTY");
  const { data, status, loading, error, mode } = useLiveMarketData(symbol, null);

  const getLiveStatusBadge = () => {
    if (mode === 'live') {
      return (
        <div className="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/40">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
          LIVE
        </div>
      );
    } else if (mode === 'snapshot') {
      return (
        <div className="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-yellow-500/20 text-yellow-400 border border-yellow-500/40">
          <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></div>
          SNAPSHOT
        </div>
      );
    } else {
      return (
        <div className="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/40">
          <div className="w-2 h-2 rounded-full bg-red-400"></div>
          {mode === 'loading' ? 'CONNECTING' : 'DISCONNECTED'}
        </div>
      );
    }
  };

  return (
    <nav className="bg-card border-b border-border">
      <div className="max-w-[1600px] mx-auto px-6 py-4">
        <div className="flex justify-between items-center">
          {/* Logo */}
          <div className="flex items-center gap-4">
            <h1 className="text-3xl font-black bg-gradient-to-r from-analytics to-bullish bg-clip-text text-transparent transform hover:scale-105 transition-transform cursor-default select-none">
              StrikeIQ
            </h1>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-6">
            {/* Symbol Selector */}
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="bg-background border border-border rounded-lg px-4 py-2 text-text-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-analytics w-32"
                placeholder="NIFTY"
              />
            </div>

            {/* Market Status Indicator */}
            <MarketStatusIndicator />

            {/* Live Status Badge */}
            {getLiveStatusBadge()}
          </div>
        </div>
      </div>
    </nav>
  );
}
