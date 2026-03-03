"use client";

import React from 'react';
import { useMarketStore } from '../stores/marketStore';

export default function MarketStatusIndicator() {
  const marketOpen = useMarketStore((s) => {
    console.log('🔍 MarketStatusIndicator: Reading marketOpen from store:', s.marketOpen)
    return s.marketOpen
  });

  // Display logic based on store state only - NO API calls
  let statusText = "Checking Market...";
  let statusColor = "bg-gray-500";
  let statusIcon = "🔄";

  console.log('🔍 MarketStatusIndicator: Current marketOpen value:', marketOpen)

  if (marketOpen === true) {
    statusText = "Market Open";
    statusColor = "bg-green-500";
    statusIcon = "🟢";
  } else if (marketOpen === false) {
    statusText = "Market Closed";
    statusColor = "bg-red-500";
    statusIcon = "🔴";
  }

  console.log('🔍 MarketStatusIndicator: Final status -', statusText, statusColor, statusIcon)

  return (
    <div className={`px-3 py-1 rounded-full text-xs font-bold ${statusColor} text-white`}>
      <span className="mr-1">{statusIcon}</span>
      {statusText}
    </div>
  );
}
