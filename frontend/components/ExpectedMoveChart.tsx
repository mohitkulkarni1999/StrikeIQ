import { RealTimeSignals } from '../types/market';
import { ArrowUp, ArrowDown, Target } from 'lucide-react';

interface ExpectedMoveChartProps {
  signals: RealTimeSignals;
}

export default function ExpectedMoveChart({ signals }: ExpectedMoveChartProps) {
  const { expected_move_signal } = signals;
  const signal = expected_move_signal.signal;
  const action = expected_move_signal.action;
  const distance = expected_move_signal.distance;

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'OVERBOUGHT':
        return 'text-danger-500';
      case 'OVERSOLD':
        return 'text-success-500';
      default:
        return 'text-warning-500';
    }
  };

  const getSignalBgColor = (signal: string) => {
    switch (signal) {
      case 'OVERBOUGHT':
        return 'bg-danger-500/20 border-danger-500/30';
      case 'OVERSOLD':
        return 'bg-success-500/20 border-success-500/30';
      default:
        return 'bg-warning-500/20 border-warning-500/30';
    }
  };

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'OVERBOUGHT':
        return <ArrowUp className="w-6 h-6" />;
      case 'OVERSOLD':
        return <ArrowDown className="w-6 h-6" />;
      default:
        return <Target className="w-6 h-6" />;
    }
  };

  // Mock expected move data - in real implementation, this would come from API
  const mockExpectedMove = {
    current_price: 19500,
    expected_move: 200,
    upper_range: 19700,
    lower_range: 19300,
    upper_percentage: 1.03,
    lower_percentage: 1.03
  };

  const rangePercentage = ((mockExpectedMove.current_price - mockExpectedMove.lower_range) / 
                          (mockExpectedMove.upper_range - mockExpectedMove.lower_range)) * 100;

  return (
    <div className="metric-card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold">Expected Move Analysis</h3>
        <div className={`px-3 py-1 rounded-full border ${getSignalBgColor(signal)}`}>
          <span className={`text-sm font-medium ${getSignalColor(signal)}`}>
            {signal}
          </span>
        </div>
      </div>

      {/* Expected Move Range Visualization */}
      <div className="mb-6">
        <div className="relative">
          {/* Range Bar */}
          <div className="h-8 bg-muted rounded-full relative overflow-hidden">
            {/* Current Position Indicator */}
            <div
              className="absolute top-0 bottom-0 w-1 bg-primary-500 z-20"
              style={{ left: `${rangePercentage}%` }}
            >
              <div className="absolute -top-2 -left-2 w-5 h-5 bg-primary-500 rounded-full border-2 border-background"></div>
            </div>
            
            {/* Range Zones */}
            <div className="absolute left-0 top-0 bottom-0 w-1/4 bg-success-500/20"></div>
            <div className="absolute left-1/4 top-0 bottom-0 w-1/2 bg-warning-500/20"></div>
            <div className="absolute right-0 top-0 bottom-0 w-1/4 bg-danger-500/20"></div>
          </div>
          
          {/* Range Labels */}
          <div className="flex justify-between mt-2 text-sm">
            <span className="text-success-500">₹{mockExpectedMove.lower_range.toLocaleString('en-IN')}</span>
            <span className="font-medium">₹{mockExpectedMove.current_price.toLocaleString('en-IN')}</span>
            <span className="text-danger-500">₹{mockExpectedMove.upper_range.toLocaleString('en-IN')}</span>
          </div>
        </div>
      </div>

      {/* Expected Move Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center">
          <div className="text-2xl font-bold text-success-500">
            -{mockExpectedMove.lower_percentage.toFixed(2)}%
          </div>
          <div className="text-sm text-muted-foreground">Lower Range</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-primary-500">
            ±{mockExpectedMove.expected_move.toFixed(0)}
          </div>
          <div className="text-sm text-muted-foreground">Expected Move</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-danger-500">
            +{mockExpectedMove.upper_percentage.toFixed(2)}%
          </div>
          <div className="text-sm text-muted-foreground">Upper Range</div>
        </div>
      </div>

      {/* Signal Analysis */}
      <div className="glass-morphism rounded-lg p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className={`p-2 rounded-lg ${getSignalBgColor(signal)}`}>
            <div className={getSignalColor(signal)}>
              {getSignalIcon(signal)}
            </div>
          </div>
          <div>
            <div className="font-medium">{signal}</div>
            <div className="text-sm text-muted-foreground">Recommended: {action}</div>
          </div>
        </div>
        
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Distance from Range</span>
            <span className="font-medium">{(distance * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Range Utilization</span>
            <span className="font-medium">{rangePercentage.toFixed(1)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Breakout Risk</span>
            <span className={`font-medium ${
              distance < 0.2 ? 'text-danger-500' : 
              distance < 0.5 ? 'text-warning-500' : 'text-success-500'
            }`}>
              {distance < 0.2 ? 'High' : distance < 0.5 ? 'Medium' : 'Low'}
            </span>
          </div>
        </div>
      </div>

      {/* Interpretation Guide */}
      <div className="mt-4 pt-4 border-t border-white/10">
        <div className="text-xs text-muted-foreground">
          <div className="font-medium mb-1">Interpretation:</div>
          <div>• Green zone: Potential oversold conditions</div>
          <div>• Yellow zone: Normal trading range</div>
          <div>• Red zone: Potential overbought conditions</div>
        </div>
      </div>
    </div>
  );
}
