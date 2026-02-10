import { RealTimeSignals } from '../types/market';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface BiasMeterProps {
  signals: RealTimeSignals;
}

export default function BiasMeter({ signals }: BiasMeterProps) {
  const { bias_signal } = signals;
  const confidence = bias_signal.confidence;
  const action = bias_signal.action;
  const strength = bias_signal.strength;

  const getBiasColor = (action: string) => {
    switch (action) {
      case 'BUY':
        return 'bias-meter-bullish';
      case 'SELL':
        return 'bias-meter-bearish';
      default:
        return 'bias-meter-neutral';
    }
  };

  const getBiasIcon = (action: string) => {
    switch (action) {
      case 'BUY':
        return <TrendingUp className="w-8 h-8" />;
      case 'SELL':
        return <TrendingDown className="w-8 h-8" />;
      default:
        return <Minus className="w-8 h-8" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 70) return 'text-success-500';
    if (confidence >= 50) return 'text-warning-500';
    return 'text-danger-500';
  };

  return (
    <div className="metric-card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold">Market Bias</h3>
        <div className="flex items-center gap-2">
          <div className="status-indicator status-online"></div>
          <span className="text-sm text-muted-foreground">Live</span>
        </div>
      </div>

      {/* Bias Meter Circle */}
      <div className="flex flex-col items-center mb-6">
        <div className={`w-32 h-32 rounded-full flex items-center justify-center text-white ${getBiasColor(action)} shadow-lg`}>
          {getBiasIcon(action)}
        </div>
        
        <div className="mt-4 text-center">
          <div className="text-2xl font-bold mb-1">{action}</div>
          <div className={`text-lg font-medium ${getConfidenceColor(confidence)}`}>
            {confidence.toFixed(1)}% Confidence
          </div>
          <div className="text-sm text-muted-foreground capitalize">
            {strength.toLowerCase()} signal
          </div>
        </div>
      </div>

      {/* Confidence Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Confidence Level</span>
          <span className={getConfidenceColor(confidence)}>{confidence.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-muted rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-500 ${
              confidence >= 70
                ? 'bg-success-500'
                : confidence >= 50
                ? 'bg-warning-500'
                : 'bg-danger-500'
            }`}
            style={{ width: `${confidence}%` }}
          ></div>
        </div>
      </div>

      {/* Bias Components */}
      <div className="mt-6 pt-6 border-t border-white/10">
        <h4 className="text-sm font-medium text-muted-foreground mb-3">Signal Components</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Bias Signal</span>
            <span className="font-medium">{bias_signal.action}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Strength</span>
            <span className="font-medium capitalize">{strength}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Last Updated</span>
            <span className="font-medium">
              {new Date(signals.timestamp).toLocaleTimeString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
