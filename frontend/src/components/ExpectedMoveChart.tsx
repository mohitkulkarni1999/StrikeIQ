import React, { memo } from 'react';
import { Target, BarChart3, TrendingUp, TrendingDown, ArrowUp, ArrowDown } from 'lucide-react';
import { toPercent } from '../utils/formatters';

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

const ExpectedMoveChart: React.FC<ExpectedMoveChartProps> = ({ probability }) => {
  // Handle missing data with skeleton (Phase 4)
  if (!probability || probability.expected_move === null || probability.expected_move === undefined) {
    return (
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 h-full flex flex-col justify-center">
        <div className="flex items-center gap-3 mb-4">
          <BarChart3 className="w-5 h-5 text-[#4F8CFF]" />
          <h3 className="text-lg font-semibold text-white">Expected Move</h3>
        </div>
        <div className="text-center text-gray-500 py-10">
          <div className="w-10 h-10 border-2 border-gray-700 border-t-gray-500 rounded-full animate-spin mx-auto mb-2" />
          <p className="text-sm font-mono tracking-wider">Calculating expected range...</p>
        </div>
      </div>
    );
  }

  const { expected_move, upper_1sd, lower_1sd, upper_2sd, lower_2sd, breach_probability, range_hold_probability, volatility_state } = probability;

  const getVolatilityStateColor = (state: string) => {
    if (!state) return 'text-[#4F8CFF] bg-[#4F8CFF]/10 border-[#4F8CFF]/30';
    switch (state.toLowerCase()) {
      case 'overpriced':
        return 'text-[#FF4D4F] bg-[#FF4D4F]/10 border-[#FF4D4F]/30';
      case 'underpriced':
        return 'text-[#00FF9F] bg-[#00FF9F]/10 border-[#00FF9F]/30';
      default:
        return 'text-[#4F8CFF] bg-[#4F8CFF]/10 border-[#4F8CFF]/30';
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
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-6 h-full transition-all">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-5 h-5 text-[#4F8CFF]" />
          <h3 className="text-lg font-semibold text-white">Expected Move</h3>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-medium ${volatilityColor}`}>
          {volatilityIcon}
          <span className="capitalize">{volatility_state || 'unknown'}</span>
        </div>
      </div>

      <div className="space-y-6">
        {/* Expected Move Metric */}
        <div className="text-center py-4 bg-black/20 rounded-xl border border-gray-800">
          <div className="text-xs text-gray-500 uppercase tracking-widest font-bold mb-1">Weekly Move</div>
          <div className="text-3xl font-black text-[#4F8CFF]">±{expected_move.toFixed(2)}</div>
        </div>

        {/* Ranges */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-800">
            <div className="text-[10px] text-gray-500 uppercase font-bold mb-2">1SD Upper</div>
            <div className="text-lg font-mono font-bold text-[#00FF9F] tracking-tight">{upper_1sd.toFixed(2)}</div>
          </div>
          <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-800">
            <div className="text-[10px] text-gray-500 uppercase font-bold mb-2">1SD Lower</div>
            <div className="text-lg font-mono font-bold text-[#FF4D4F] tracking-tight">{lower_1sd.toFixed(2)}</div>
          </div>
        </div>

        {/* Probability Info */}
        <div className="bg-gray-800/30 p-4 rounded-xl border border-gray-800">
          <div className="flex items-center justify-between text-sm mb-4">
            <span className="text-gray-400">Prob. of Breach</span>
            <span className="font-black text-[#FFC857]">{toPercent(breach_probability).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-black/30 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-[#FFC857] h-full rounded-full transition-all duration-1000"
              style={{ width: `${toPercent(breach_probability)}%` }}
            />
          </div>
          <div className="mt-3 text-[10px] text-gray-500 leading-tight">
            Historical data suggests a <span className="text-gray-300">{toPercent(range_hold_probability).toFixed(1)}%</span> chance of settling within 1SD range.
          </div>
        </div>
      </div>
    </div>
  );
};

export default memo(ExpectedMoveChart);
