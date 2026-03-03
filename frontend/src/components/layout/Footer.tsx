"use client";

import React, { useState } from "react";
import { Settings, TrendingUp, Activity, BarChart3 } from "lucide-react";
import { useMarketStore } from "@/stores/marketStore";

const SYMBOLS = ['NIFTY', 'BANKNIFTY', 'FINNIFTY'] as const;
type Symbol = typeof SYMBOLS[number];

export interface FooterProps {
  onSymbolSelect?: (symbol: Symbol) => void;
}

export default function Footer({ onSymbolSelect }: FooterProps) {
  const marketOpen = useMarketStore((s) => s.marketOpen);
  const [activeTab, setActiveTab] = useState<'oi' | 'volume' | 'vwap'>('oi');

  // Footer uses only store state - NO API calls
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-sm border-t border-gray-800/50 z-20">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between">

          {/* Market Status - Store Only */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">Market:</span>
            <div className={`px-2 py-1 rounded text-xs font-bold ${marketOpen === true ? 'bg-green-500/20 text-green-400 border border-green-500/30' :
                marketOpen === false ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                  'bg-gray-500/20 text-gray-400 border border-gray-500/30'
              }`}>
              {marketOpen === true ? 'OPEN' : marketOpen === false ? 'CLOSED' : 'CHECKING'}
            </div>
          </div>

          {/* Symbol Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">Symbol:</span>
            <div className="flex gap-1">
              {SYMBOLS.map((sym) => (
                <button
                  key={sym}
                  onClick={() => onSymbolSelect?.(sym)}
                  className={`px-2 py-1 rounded text-xs font-mono transition-colors ${sym === SYMBOLS[0] ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
                      'bg-gray-700/50 text-gray-300 border border-gray-600/30 hover:bg-gray-600/50'
                    }`}
                >
                  {sym}
                </button>
              ))}
            </div>
          </div>

          {/* Analysis Tabs */}
          <div className="flex items-center gap-1 bg-gray-800/50 rounded-lg p-1">
            {[
              { id: 'oi', label: 'OI Analysis', icon: BarChart3 },
              { id: 'volume', label: 'Volume', icon: TrendingUp },
              { id: 'vwap', label: 'VWAP', icon: Activity },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${activeTab === tab.id
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-400 hover:text-gray-200'
                  }`}
              >
                <tab.icon size={12} />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            ))}
          </div>

          {/* Settings */}
          <button className="p-2 rounded-lg text-gray-400 hover:text-gray-200 transition-colors">
            <Settings size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
