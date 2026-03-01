import React, { memo } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  ArrowUpRight, 
  ArrowDownRight, 
  Shield, 
  Clock,
  AlertTriangle,
  Info
} from 'lucide-react';

interface TradeSignalCardProps {
  signal: {
    symbol: string;
    strategy: string;
    option: string;
    entry: number;
    target: number;
    stoploss: number;
    risk_reward: number;
    confidence: number;
    regime: string;
    timestamp?: string;
    reason?: string;
  };
}

function TradeSignalCard({ signal }: TradeSignalCardProps) {
  const getStrategyColor = (strategy: string) => {
    switch (strategy?.toLowerCase()) {
      case 'bull_call':
      case 'bull_put':
        return 'text-[#00FF9F] bg-[#00FF9F]/10 border-[#00FF9F]/30';
      case 'bear_call':
      case 'bear_put':
        return 'text-[#FF4D4F] bg-[#FF4D4F]/10 border-[#FF4D4F]/30';
      case 'iron_condor':
      case 'strangle':
        return 'text-[#4F8CFF] bg-[#4F8CFF]/10 border-[#4F8CFF]/30';
      default:
        return 'text-[#FFC857] bg-[#FFC857]/10 border-[#FFC857]/30';
    }
  };

  const getRegimeColor = (regime: string) => {
    switch (regime?.toLowerCase()) {
      case 'bullish':
      case 'uptrend':
        return 'text-[#00FF9F]';
      case 'bearish':
      case 'downtrend':
        return 'text-[#FF4D4F]';
      default:
        return 'text-[#4F8CFF]';
    }
  };

  const getRiskRewardColor = (rr: number) => {
    if (rr >= 3) return 'text-[#00FF9F]';
    if (rr >= 2) return 'text-[#FFC857]';
    return 'text-[#FF4D4F]';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 75) return 'text-[#00FF9F]';
    if (confidence >= 50) return 'text-[#FFC857]';
    return 'text-[#FF4D4F]';
  };

  const isProfitable = signal.target > signal.entry;
  const riskPercentage = ((signal.entry - signal.stoploss) / signal.entry) * 100;
  const rewardPercentage = ((signal.target - signal.entry) / signal.entry) * 100;

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 hover:border-[#374151] transition-all duration-300">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            {isProfitable ? (
              <ArrowUpRight className="w-5 h-5 text-[#00FF9F]" />
            ) : (
              <ArrowDownRight className="w-5 h-5 text-[#FF4D4F]" />
            )}
            <div>
              <h3 className="text-lg font-bold text-white">{signal.symbol}</h3>
              <p className="text-sm text-gray-400">{signal.option}</p>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <div className={`px-3 py-1 rounded-full border text-xs font-medium ${getStrategyColor(signal.strategy)}`}>
            <span className="capitalize">{signal.strategy.replace('_', ' ')}</span>
          </div>
          <div className={`text-xs font-medium ${getRegimeColor(signal.regime)}`}>
            {signal.regime.toUpperCase()}
          </div>
        </div>
      </div>

      {/* Price Levels */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className="text-xs text-gray-400 mb-1">Entry</div>
          <div className="text-lg font-bold text-white">
            {signal.entry.toLocaleString('en-IN')}
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-xs text-gray-400 mb-1">Target</div>
          <div className={`text-lg font-bold ${isProfitable ? 'text-[#00FF9F]' : 'text-[#FF4D4F]'}`}>
            {signal.target.toLocaleString('en-IN')}
          </div>
          <div className={`text-xs ${isProfitable ? 'text-[#00FF9F]/70' : 'text-[#FF4D4F]/70'}`}>
            +{rewardPercentage.toFixed(1)}%
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-xs text-gray-400 mb-1">Stoploss</div>
          <div className="text-lg font-bold text-[#FF4D4F]">
            {signal.stoploss.toLocaleString('en-IN')}
          </div>
          <div className="text-xs text-[#FF4D4F]/70">
            -{riskPercentage.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-black/30 rounded-lg p-3 border border-white/10">
          <div className="flex items-center gap-2 mb-1">
            <Target className="w-4 h-4 text-[#4F8CFF]" />
            <span className="text-xs text-gray-400">Risk/Reward</span>
          </div>
          <div className={`text-lg font-bold ${getRiskRewardColor(signal.risk_reward)}`}>
            1:{signal.risk_reward.toFixed(1)}
          </div>
        </div>

        <div className="bg-black/30 rounded-lg p-3 border border-white/10">
          <div className="flex items-center gap-2 mb-1">
            <Shield className="w-4 h-4 text-[#4F8CFF]" />
            <span className="text-xs text-gray-400">Confidence</span>
          </div>
          <div className={`text-lg font-bold ${getConfidenceColor(signal.confidence)}`}>
            {signal.confidence.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Risk Indicator */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-400">Risk Level</span>
          <div className="flex items-center gap-1">
            <AlertTriangle className={`w-3 h-3 ${signal.risk_reward >= 2 ? 'text-[#00FF9F]' : signal.risk_reward >= 1.5 ? 'text-[#FFC857]' : 'text-[#FF4D4F]'}`} />
            <span className={`text-xs font-medium ${signal.risk_reward >= 2 ? 'text-[#00FF9F]' : signal.risk_reward >= 1.5 ? 'text-[#FFC857]' : 'text-[#FF4D4F]'}`}>
              {signal.risk_reward >= 3 ? 'LOW' : signal.risk_reward >= 2 ? 'MEDIUM' : 'HIGH'}
            </span>
          </div>
        </div>
        <div className="w-full h-2 bg-black/30 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              signal.risk_reward >= 3 ? 'bg-[#00FF9F]' :
              signal.risk_reward >= 2 ? 'bg-[#FFC857]' :
              'bg-[#FF4D4F]'
            }`}
            style={{ width: `${Math.min(100, (signal.risk_reward / 3) * 100)}%` }}
          />
        </div>
      </div>

      {/* Reason */}
      {signal.reason && (
        <div className="bg-black/20 rounded-lg p-3 border border-white/5">
          <div className="flex items-center gap-2 mb-2">
            <Info className="w-4 h-4 text-[#4F8CFF]" />
            <span className="text-xs font-medium text-gray-300">Trade Rationale</span>
          </div>
          <div className="text-xs text-gray-400 leading-relaxed">
            {signal.reason}
          </div>
        </div>
      )}

      {/* Timestamp */}
      {signal.timestamp && (
        <div className="flex items-center gap-2 mt-3 text-xs text-gray-500">
          <Clock className="w-3 h-3" />
          <span>{new Date(signal.timestamp).toLocaleString()}</span>
        </div>
      )}
    </div>
  );
}

export default memo(TradeSignalCard);
