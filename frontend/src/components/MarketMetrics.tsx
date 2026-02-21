import React from 'react';
import { TrendingUp, TrendingDown, Target, Activity, BarChart3, Clock } from 'lucide-react';

interface MarketMetricsProps {
  analytics: {
    spot: number;
    change: number;
    changePercent: number;
    high: number;
    low: number;
    volume: number;
    vwap: number;
    timestamp?: string;
  };
}

export default function MarketMetrics({ analytics }: MarketMetricsProps) {
  // FIX 5: Never return null silently — show skeleton instead
  if (!analytics || analytics.spot === 0 && analytics.volume === 0) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-[#111827] border border-[#1F2937] rounded-xl p-4 animate-pulse">
            <div className="h-3 bg-gray-800 rounded w-1/2 mb-3" />
            <div className="h-6 bg-gray-700 rounded w-3/4 mb-2" />
            <div className="h-3 bg-gray-800 rounded w-1/3" />
          </div>
        ))}
      </div>
    );
  }

  const { spot, change, changePercent, high, low, volume, vwap } = analytics;
  const isPositive = change >= 0;

  const metricItems = [
    {
      label: "Live Spot",
      value: spot?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
      subValue: `${isPositive ? '+' : ''}${change?.toFixed(2)} (${isPositive ? '+' : ''}${changePercent?.toFixed(2)}%)`,
      type: isPositive ? 'positive' : 'negative',
      icon: isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />
    },
    {
      label: "Day Range",
      value: `${high?.toLocaleString('en-IN')} - ${low?.toLocaleString('en-IN')}`,
      subValue: "H / L Intensity",
      type: 'neutral',
      icon: <Activity className="w-5 h-5" />
    },
    {
      label: "Total Volume (OI)",
      value: (volume / 10000000).toFixed(2) + " Cr",
      subValue: "Cumulative Multi-Symbol",
      type: 'neutral',
      icon: <BarChart3 className="w-5 h-5" />
    },
    {
      label: "VWAP Variance",
      value: vwap?.toLocaleString('en-IN', { minimumFractionDigits: 2 }),
      subValue: spot > vwap ? "Above VWAP (Bullish)" : "Below VWAP (Bearish)",
      type: spot > vwap ? 'positive' : 'negative',
      icon: <Target className="w-5 h-5" />
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metricItems.map((item, index) => (
        <div key={index} className="bg-[#111827] border border-[#1F2937] rounded-xl p-4 hover:border-gray-700 transition-all group">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">{item.label}</span>
            <div className={`p-2 rounded-lg ${item.type === 'positive' ? 'bg-[#00FF9F]/10 text-[#00FF9F]' :
              item.type === 'negative' ? 'bg-[#FF4D4F]/10 text-[#FF4D4F]' :
                'bg-[#4F8CFF]/10 text-[#4F8CFF]'
              }`}>
              {item.icon}
            </div>
          </div>
          <div className="text-xl font-bold text-white mb-1">{item.value || '0.00'}</div>
          <div className={`text-xs font-semibold ${item.type === 'positive' ? 'text-[#00FF9F]' :
            item.type === 'negative' ? 'text-[#FF4D4F]' :
              'text-gray-400'
            }`}>
            {item.subValue}
          </div>
        </div>
      ))}
    </div>
  );
}
