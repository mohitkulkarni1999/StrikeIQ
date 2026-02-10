import { MarketData } from '../types/market';
import { BarChart3, TrendingUp, Users, Activity } from 'lucide-react';

interface MarketMetricsProps {
  data: MarketData;
}

export default function MarketMetrics({ data }: MarketMetricsProps) {
  const { current_market, real_time_signals } = data;

  // Mock additional metrics - in real implementation, these would come from API
  const mockMetrics = {
    total_oi: 12500000,
    total_volume: 850000,
    vwap: current_market.vwap,
    price_change: current_market.change,
    volatility: 18.5,
    market_sentiment: 'Bullish',
    participation_score: 75
  };

  const metrics = [
    {
      label: 'Total OI',
      value: (mockMetrics.total_oi / 10000000).toFixed(2) + ' Cr',
      change: '+2.5%',
      changeType: 'positive' as const,
      icon: <BarChart3 className="w-5 h-5" />,
      color: 'text-primary-500'
    },
    {
      label: 'Total Volume',
      value: (mockMetrics.total_volume / 100000).toFixed(1) + ' L',
      change: '+5.2%',
      changeType: 'positive' as const,
      icon: <Activity className="w-5 h-5" />,
      color: 'text-success-500'
    },
    {
      label: 'VWAP',
      value: '₹' + mockMetrics.vwap.toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }),
      change: ((current_market.spot_price - mockMetrics.vwap) / mockMetrics.vwap * 100).toFixed(2) + '%',
      changeType: current_market.spot_price > mockMetrics.vwap ? 'positive' as const : 'negative' as const,
      icon: <TrendingUp className="w-5 h-5" />,
      color: 'text-warning-500'
    },
    {
      label: 'Participation',
      value: mockMetrics.participation_score + '%',
      change: '+3.1%',
      changeType: 'positive' as const,
      icon: <Users className="w-5 h-5" />,
      color: 'text-info-500'
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
      <div className="glass-morphism rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium">Market Sentiment</h4>
          <div className={`px-3 py-1 rounded-full ${
            mockMetrics.market_sentiment === 'Bullish' 
              ? 'bg-success-500/20 text-success-500' 
              : mockMetrics.market_sentiment === 'Bearish'
              ? 'bg-danger-500/20 text-danger-500'
              : 'bg-warning-500/20 text-warning-500'
          }`}>
            {mockMetrics.market_sentiment}
          </div>
        </div>
        
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Volatility</span>
            <span className="font-medium">{mockMetrics.volatility}%</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Price vs VWAP</span>
            <span className={`font-medium ${
              current_market.spot_price > mockMetrics.vwap ? 'text-success-500' : 'text-danger-500'
            }`}>
              {current_market.spot_price > mockMetrics.vwap ? 'Above' : 'Below'}
            </span>
          </div>
        </div>
      </div>

      {/* Signal Strength */}
      <div className="space-y-3">
        <h4 className="text-sm font-medium text-muted-foreground">Signal Strength</h4>
        
        <div className="space-y-2">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-muted-foreground">Bias Signal</span>
              <span className="font-medium">{real_time_signals.bias_signal.strength}</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  real_time_signals.bias_signal.strength === 'STRONG' 
                    ? 'bg-success-500 w-4/5'
                    : real_time_signals.bias_signal.strength === 'MODERATE'
                    ? 'bg-warning-500 w-1/2'
                    : 'bg-danger-500 w-1/4'
                }`}
              ></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-muted-foreground">Overall Signal</span>
              <span className="font-medium">{real_time_signals.overall_signal.strength}</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  real_time_signals.overall_signal.strength === 'STRONG' 
                    ? 'bg-success-500 w-4/5'
                    : real_time_signals.overall_signal.strength === 'MODERATE'
                    ? 'bg-warning-500 w-1/2'
                    : 'bg-danger-500 w-1/4'
                }`}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
