import { BarChart3, TrendingUp, Activity } from 'lucide-react';

interface AnalyticsData {
  total_call_oi: number;
  total_put_oi: number;
  pcr: number;
  strongest_support: number;
  strongest_resistance: number;
}

interface MarketMetricsProps {
  analytics: AnalyticsData;
}

export default function MarketMetrics({ analytics }: MarketMetricsProps) {
  console.log('MarketMetrics render - analytics:', analytics);
  
  // Compute real metrics from analytics
  const totalCallOI = analytics?.total_call_oi ?? 0;
  const totalPutOI = analytics?.total_put_oi ?? 0;
  const totalOI = totalCallOI + totalPutOI;

  const pcr = analytics?.pcr ?? 0;

  const sentiment =
    pcr > 1.2
      ? "Bullish"
      : pcr < 0.8
      ? "Bearish"
      : "Neutral";

  const biasStrength = Math.min(Math.abs(pcr - 1) * 100, 100);

  // Safe VWAP calculation (no division by zero)
  const vwapChange =
    totalOI > 0
      ? ((0 - totalOI) / totalOI) * 100  // Removed data.spot_price reference
      : 0;

  const metrics = [
    {
      label: "Total OI",
      value: (totalOI / 10000000).toFixed(2) + " Cr",
      change: "PCR: " + pcr.toFixed(2),
      changeType: pcr > 1 ? ("positive" as const) : ("negative" as const),
      icon: <BarChart3 className="w-5 h-5" />,
      color: "text-primary-500"
    },
    {
      label: "Call OI",
      value: totalCallOI.toLocaleString("en-IN"),
      change: "Resistance @ " + (analytics?.strongest_resistance ?? "-"),
      changeType: "negative" as const,
      icon: <BarChart3 className="w-5 h-5" />,
      color: "text-danger-500"
    },
    {
      label: "Put OI",
      value: totalPutOI.toLocaleString("en-IN"),
      change: "Support @ " + (analytics?.strongest_support ?? "-"),
      changeType: "positive" as const,
      icon: <BarChart3 className="w-5 h-5" />,
      color: "text-success-500"
    }
  ];

  const getChangeColor = (changeType: 'positive' | 'negative') => {
    return changeType === 'positive' ? 'text-success-500' : 'text-danger-500';
  };

  const getChangeBgColor = (changeType: 'positive' | 'negative') => {
    return changeType === 'positive' ? 'bg-success-500/20' : 'bg-danger-500/20';
  };

  return (
    <div className="metric-card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold">Market Metrics</h3>
        <div className="text-sm text-muted-foreground">
          {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {metrics.map((metric, index) => (
          <div key={index} className="glass-morphism rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className={`${metric.color}`}>
                {metric.icon}
              </div>
              <div className={`text-xs px-2 py-1 rounded-full ${getChangeBgColor(metric.changeType)} ${getChangeColor(metric.changeType)}`}>
                {metric.change}
              </div>
            </div>
            <div className="text-lg font-bold mb-1">{metric.value}</div>
            <div className="text-xs text-muted-foreground">{metric.label}</div>
          </div>
        ))}
      </div>

      {/* Market Sentiment */}
      <div className="glass-morphism rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium mb-3">Market Sentiment</h4>
          <div className={`px-3 py-1 rounded-full ${
            sentiment === 'Bullish' 
              ? 'bg-success-500/20 text-success-500' 
              : sentiment === 'Bearish'
              ? 'bg-danger-500/20 text-danger-500'
              : 'bg-warning-500/20 text-warning-500'
          }`}>
            {sentiment}
          </div>
        </div>
        
        <div className="space-y-2">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-muted-foreground">Put/Call Ratio</span>
            <span className="font-medium">{pcr.toFixed(2)}</span>
          </div>
          <div className="h-2 rounded-full bg-gray-500/20">
            <div
              className="h-2 rounded-full bg-primary-500"
              style={{ width: `${biasStrength}%` }}
            ></div>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Market Bias</span>
            <span className={`font-medium ${
              sentiment === 'Bullish' ? 'text-success-500' : 'text-danger-500'
            }`}>
              {sentiment}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
