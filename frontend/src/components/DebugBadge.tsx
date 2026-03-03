"use client";

import React from 'react';
import { useWSStore } from '../core/ws/wsStore';
import { useMarketStore } from '../stores/marketStore';

interface DebugBadgeProps {
  className?: string;
}

export default function DebugBadge({ className }: DebugBadgeProps) {
  const connected = useWSStore((s) => s.connected);
  const marketOpen = useMarketStore((s) => s.marketOpen);

  // Debug component uses only store state - NO API calls
  return (
    <div className={`fixed top-4 right-4 bg-black/80 text-white p-2 rounded text-xs font-mono z-50 ${className || ''}`}>
      <div>WS: {connected ? '🟢' : '🔴'}</div>
      <div>Market: {marketOpen === true ? 'OPEN' : marketOpen === false ? 'CLOSED' : 'CHECKING'}</div>
    </div>
  );
}
