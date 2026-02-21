import React from 'react';
import { TrendingUp, TrendingDown, BarChart3, AlertTriangle, Target, Activity } from 'lucide-react';

interface ProbabilityDisplayProps {
  probability?: any;
}

export default function ProbabilityDisplay({ probability }: ProbabilityDisplayProps) {
  console.log('🔍 ProbabilityDisplay - Received probability:', probability);

  if (!probability) {
    return (
      <div className="glass-morphism rounded-2xl p-6 border border-white/10">
        <div className="flex items-center gap-3 mb-4">
          <BarChart3 className="w-5 h-5 text-primary-400" />
          <h3 className="text-lg font-semibold text-white">Probability Metrics</h3>
        </div>
        <div className="text-center text-muted-foreground">
          <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>Probability data unavailable</p>
        </div>
      </div>
    );
  }

  const getVolatilityStateColor = (state: string) => {
    switch (state) {
      case 'overpriced':
        return 'text-danger-400 bg-danger-500/20 border-danger-500/30';
      case 'underpriced':
        return 'text-success-400 bg-success-500/20 border-success-500/30';
      default:
        return 'text-blue-400 bg-blue-500/20 border-blue-500/30';
    }
  };

  const getVolatilityStateIcon = (state: string) => {
    switch (state) {
      case 'overpriced':
        return <TrendingUp className="w-4 h-4" />;
      case 'underpriced':
        return <TrendingDown className="w-4 h-4" />;
      default:
        return <Target className="w-4 h-4" />;
    }
  };

  return (
    <div className="glass-morphism rounded-2xl p-6 border border-white/10">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-5 h-5 text-primary-400" />
          <h3 className="text-lg font-semibold text-white">Probability Metrics</h3>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-medium ${getVolatilityStateColor(probability.volatility_state)}`}>
          {getVolatilityStateIcon(probability.volatility_state)}
          <span className="capitalize">{probability.volatility_state}</span>
        </div>
      </div>

      <div className="space-y-6">
        {/* Expected Move */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Expected Move (1SD)</span>
            <span className="text-xl font-bold text-primary-400">
              ±{probability.expected_move?.toFixed(2) || '0.00'}
            </span>
          </div>
          <div className="text-xs text-muted-foreground">
            Based on ATM straddle pricing
          </div>
        </div>

        {/* Range Display */}
        <div>
          <h4 className="text-sm font-medium text-white mb-3">Probability Ranges</h4>

          {/* 1SD Range */}
          <div className="mb-4 p-4 rounded-lg border border-white/10 bg-black/20">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">1SD Range (68% prob)</span>
              <span className="text-sm font-medium text-blue-400">
                {probability.range_hold_probability?.toFixed(1) || '0.0'}%
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-danger-400">
                ↓ {probability.lower_1sd?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              </span>
              <span className="text-success-400">
                ↑ {probability.upper_1sd?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              </span>
            </div>
          </div>

          {/* 2SD Range */}
          <div className="p-4 rounded-lg border border-white/10 bg-black/20">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">2SD Range (95% prob)</span>
              <span className="text-sm font-medium text-warning-400">
                {(100 - (probability.breach_probability?.toFixed(1) || 0))}%
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-danger-400">
                ↓ {probability.lower_2sd?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              </span>
              <span className="text-success-400">
                ↑ {probability.upper_2sd?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              </span>
            </div>
          </div>
        </div>

        {/* Breach Probability */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-white">Range Breach Risk</span>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-warning-400" />
              <span className="text-sm font-bold text-warning-400">
                {probability.breach_probability?.toFixed(1) || '0.0'}%
              </span>
            </div>
          </div>
          <div className="w-full h-2 bg-black/30 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-success-500 via-warning-500 to-danger-500 transition-all duration-500"
              style={{ width: `${probability.breach_probability || 0}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>Low Risk</span>
            <span>High Risk</span>
          </div>
        </div>
      </div>
    </div>
  );
}
