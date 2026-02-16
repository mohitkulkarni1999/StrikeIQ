import React from 'react';
import { ArrowUp, ArrowDown, Target, BarChart3 } from 'lucide-react';

interface ExpectedMoveChartProps {
  probability?: {
    expected_move: number;
    upper_1sd: number;
    lower_1sd: number;
    upper_2sd: number;
    lower_2sd: number;
    breach_probability: number;
    range_hold_probability: number;
    volatility_state: string;
  };
}

export default function ExpectedMoveChart({ probability }: ExpectedMoveChartProps) {
  console.log('🔍 ExpectedMoveChart - Received probability:', probability);
  
  if (!probability || probability.expected_move === null || probability.expected_move === undefined) {
    return (
      <div className="glass-morphism rounded-2xl p-6 border border-white/10">
        <div className="flex items-center gap-3 mb-4">
          <BarChart3 className="w-5 h-5 text-primary-400" />
          <h3 className="text-lg font-semibold text-white">Expected Move Analysis</h3>
        </div>
        <div className="text-center text-muted-foreground">
          <Target className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>Expected move data unavailable</p>
        </div>
      </div>
    );
  }

  const { expected_move, upper_1sd, lower_1sd, upper_2sd, lower_2sd, breach_probability, range_hold_probability, volatility_state } = probability;

  const getVolatilityStateColor = (state: string) => {
    if (!state) return 'text-blue-400 bg-blue-500/20 border-blue-500/30';
    switch (state.toLowerCase()) {
      case 'overpriced':
        return 'text-danger-400 bg-danger-500/20 border-danger-500/30';
      case 'underpriced':
        return 'text-success-400 bg-success-500/20 border-success-500/30';
      default:
        return 'text-blue-400 bg-blue-500/20 border-blue-500/30';
    }
  };

  const getVolatilityStateIcon = (state: string) => {
    if (!state) return <Target className="w-4 h-4" />;
    switch (state.toLowerCase()) {
      case 'overpriced':
        return <ArrowUp className="w-4 h-4" />;
      case 'underpriced':
        return <ArrowDown className="w-4 h-4" />;
      default:
        return <Target className="w-4 h-4" />;
    }
  };

  const volatilityColor = getVolatilityStateColor(volatility_state);
  const volatilityIcon = getVolatilityStateIcon(volatility_state);

  return (
    <div className="glass-morphism rounded-2xl p-6 border border-white/10">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-5 h-5 text-primary-400" />
          <h3 className="text-lg font-semibold text-white">Expected Move Analysis</h3>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-medium ${volatilityColor}`}>
          {volatilityIcon}
          <span className="capitalize">{volatility_state || 'unknown'}</span>
        </div>
      </div>

      <div className="space-y-6">
        <div className="text-center">
          <div className="text-3xl font-bold text-primary-400">
            ±{expected_move.toFixed(2)}
          </div>
          <div className="text-sm text-muted-foreground">
            Expected Move (1SD)
          </div>
        </div>

        <div className="space-y-4">
          <div className="p-4 rounded-lg border border-white/10 bg-black/20">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">1SD Range (68% prob)</span>
              <span className="text-sm font-medium text-blue-400">
                {range_hold_probability?.toFixed(1) || '0.0'}%
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-red-400">
                ↓ {lower_1sd?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              </span>
              <span className="text-green-400">
                ↑ {upper_1sd?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              </span>
            </div>
          </div>

          <div className="p-4 rounded-lg border border-white/10 bg-black/20">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">2SD Range (95% prob)</span>
              <span className="text-sm font-medium text-warning-400">
                {(100 - Number(breach_probability?.toFixed(1) || 0))}%
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-red-300">
                ↓ {lower_2sd?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              </span>
              <span className="text-green-300">
                ↑ {upper_2sd?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mt-4">
          <div className="text-center">
            <div className="text-lg font-semibold text-blue-400">
              {breach_probability?.toFixed(1) || '0.0'}%
            </div>
            <div className="text-xs text-muted-foreground">
              Breach Probability
            </div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-green-400">
              {range_hold_probability?.toFixed(1) || '0.0'}%
            </div>
            <div className="text-xs text-muted-foreground">
              Range Hold Probability
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
