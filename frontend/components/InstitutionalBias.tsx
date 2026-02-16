import React from 'react';
import { TrendingUp, TrendingDown, Minus, Target, Activity, AlertTriangle, Zap } from 'lucide-react';

interface InstitutionalBiasProps {
  intelligence?: {
    bias: {
      score: number;
      label: string;
      strength: number;
      direction: string;
      confidence: number;
      signal: string;
    };
    volatility: {
      current: string;
      percentile: number;
      trend: string;
      risk: string;
      environment: string;
    };
    liquidity: {
      total_oi: number;
      oi_change_24h: number;
      concentration: number;
      depth_score: number;
      flow_direction: string;
    };
  };
  spotPrice?: number;
  marketStatus?: string;
  marketChange?: number;
  marketChangePercent?: number;
}

export default function InstitutionalBias({ intelligence, spotPrice, marketStatus, marketChange, marketChangePercent }: InstitutionalBiasProps) {
  console.log('🔍 InstitutionalBias - Received intelligence:', intelligence);
  
  if (!intelligence) {
    return (
      <div className="glass-morphism rounded-2xl p-6 border border-white/10">
        <div className="flex items-center gap-3 mb-4">
          <Target className="w-5 h-5 text-primary-400" />
          <h3 className="text-lg font-semibold text-white">Institutional Bias</h3>
        </div>
        <div className="text-center text-muted-foreground">
          <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>Loading intelligence...</p>
        </div>
      </div>
    );
  }

  const biasScore = intelligence.bias?.score ?? 0;
  const biasLabel = intelligence.bias?.label ?? "NEUTRAL";
  const oiDominance = intelligence.liquidity?.concentration ? (intelligence.liquidity.concentration - 0.5) * 2 : 0;
  const positionScore = intelligence.liquidity?.depth_score ? intelligence.liquidity.depth_score - 0.5 : 0;
  const strongestSupport = 0; // This would be part of analytics in full implementation
  const strongestResistance = 0; // This would be part of analytics in full implementation

  // Direction indicator
  const getDirectionIcon = () => {
    if (biasLabel.includes("BULL")) {
      return <TrendingUp className="w-6 h-6 text-success-500" />;
    } else if (biasLabel.includes("BEAR")) {
      return <TrendingDown className="w-6 h-6 text-danger-500" />;
    } else {
      return <Minus className="w-6 h-6 text-warning-500" />;
    }
  };

  // Color scheme based on bias
  const getBiasColorScheme = () => {
    if (biasLabel.includes("BULL")) {
      return {
        bg: "bg-gradient-to-br from-success-500/20 to-emerald-500/10",
        border: "border-success-500/30",
        glow: "shadow-success-500/20",
        bar: "bg-gradient-to-r from-success-500 to-emerald-500"
      };
    } else if (biasLabel.includes("BEAR")) {
      return {
        bg: "bg-gradient-to-br from-danger-500/20 to-red-500/10",
        border: "border-danger-500/30",
        glow: "shadow-danger-500/20",
        bar: "bg-gradient-to-r from-danger-500 to-red-500"
      };
    } else {
      return {
        bg: "bg-gradient-to-br from-warning-500/20 to-amber-500/10",
        border: "border-warning-500/30",
        glow: "shadow-warning-500/20",
        bar: "bg-gradient-to-r from-warning-500 to-amber-500"
      };
    }
  };

  const colorScheme = getBiasColorScheme();

  // Generate insight sentence
  const generateInsight = () => {
    if (biasLabel.includes("BULL")) {
      return `Institutions are aggressively positioning for upside above ${strongestResistance.toLocaleString('en-IN')}.`;
    } else if (biasLabel.includes("BEAR")) {
      return `Strong put dominance at ${strongestSupport.toLocaleString('en-IN')} strike indicates defensive positioning.`;
    } else {
      return `Balanced institutional activity around current price levels.`;
    }
  };

  const getSecondaryInsight = () => {
    if (Math.abs(oiDominance) > 0.3) {
      return `${Math.abs(oiDominance * 100).toFixed(1)}% ${oiDominance > 0 ? 'put' : 'call'} dominance detected.`;
    } else {
      return `OI balance suggests ${biasLabel.toLowerCase()} market structure.`;
    }
  };

  return (
    <div className={`glass-morphism rounded-2xl p-6 border ${colorScheme.border} ${colorScheme.bg} ${colorScheme.glow} shadow-2xl relative overflow-hidden lg:sticky lg:top-6`}>
      {/* Animated gradient background overlay */}
      <div className={`absolute inset-0 bg-gradient-to-br ${biasLabel.includes("BULL") ? 'from-success-500/5 to-emerald-500/5' : biasLabel.includes("BEAR") ? 'from-danger-500/5 to-red-500/5' : 'from-warning-500/5 to-amber-500/5'} opacity-50`}></div>
      
      {/* Content */}
      <div className="relative z-10">
        {/* Header with Integrated Market Data */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Target className="w-5 h-5 text-primary-400" />
            <h2 className="text-xl font-bold text-white tracking-wide">Institutional Bias</h2>
          </div>
          <div className="flex items-center gap-4">
            {/* Market Status */}
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                marketStatus === 'OPEN' ? 'bg-success-500' : 'bg-danger-500'
              }`}></div>
              <span className="capitalize text-xs text-muted-foreground">
                {marketStatus || 'Loading...'}
              </span>
            </div>
            {/* Spot Price */}
            <div className="text-right">
              <div className="text-2xl font-black text-white">
                {spotPrice ? `₹${spotPrice.toLocaleString('en-IN', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}` : '₹--'}
              </div>
              {marketChange !== undefined && marketChange !== null && (
                <div className={`text-sm font-bold ${
                  marketChange >= 0 ? 'text-success-500' : 'text-danger-500'
                }`}>
                  {marketChange >= 0 ? '+' : ''}
                  {marketChange.toFixed(2)} ({marketChangePercent && marketChangePercent >= 0 ? '+' : ''}{marketChangePercent ? (marketChangePercent * 100).toFixed(2) : '0.00'}%)
                </div>
              )}
            </div>
            {getDirectionIcon()}
            <div className={`px-4 py-2 rounded-full font-bold text-sm ${
              biasLabel.includes("BULL") ? "bg-success-500/20 text-success-400 border border-success-500/30" :
              biasLabel.includes("BEAR") ? "bg-danger-500/20 text-danger-400 border border-danger-500/30" :
              "bg-warning-500/20 text-warning-400 border border-warning-500/30"
            }`}>
              {biasLabel.replace("_", " ")}
            </div>
          </div>
        </div>

        {/* Hero Bias Score */}
        <div className="text-center mb-8">
          <div className="text-7xl font-black text-white mb-1 tracking-tight">
            {biasScore}
            <span className="text-2xl font-light text-white/50">/100</span>
          </div>
          <div className="text-sm text-muted-foreground mb-4">Bias Strength Score</div>
          
          {/* Animated Progress Bar */}
          <div className="w-full h-4 bg-black/30 rounded-full overflow-hidden backdrop-blur-sm">
            <div 
              className={`h-full ${colorScheme.bar} transition-all duration-1000 ease-out relative overflow-hidden`}
              style={{ width: `${biasScore}%` }}
            >
              {/* Animated shimmer effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
            </div>
          </div>
        </div>

        {/* Volatility Regime */}
        <div className="mb-6 p-4 rounded-xl border border-white/10 bg-black/20 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-primary-400" />
              <span className="text-sm font-medium text-white">Volatility Regime</span>
            </div>
            <div className={`px-3 py-1 rounded-full text-xs font-bold ${
              intelligence.volatility.current === 'extreme' ? 'bg-danger-500/20 text-danger-400 border border-danger-500/30' :
              intelligence.volatility.current === 'elevated' ? 'bg-warning-500/20 text-warning-400 border border-warning-500/30' :
              intelligence.volatility.current === 'normal' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' :
              'bg-success-500/20 text-success-400 border border-success-500/30'
            }`}>
              {intelligence.volatility.current.toUpperCase()}
            </div>
          </div>
          
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Risk Environment</span>
            <span className={`font-medium capitalize ${
              intelligence.volatility.risk === 'extreme' ? 'text-danger-400' :
              intelligence.volatility.risk === 'high' ? 'text-warning-400' :
              intelligence.volatility.risk === 'medium' ? 'text-blue-400' :
              'text-success-400'
            }`}>
              {intelligence.volatility.risk}
            </span>
          </div>
          
          <div className="flex items-center justify-between text-sm mt-2">
            <span className="text-muted-foreground">Market Phase</span>
            <span className="font-medium capitalize text-primary-400">
              {intelligence.volatility.environment}
            </span>
          </div>
        </div>

        {/* Quick Insights */}
        <div className="space-y-4 mb-6">
          <div className="flex items-start gap-3">
            <Activity className="w-4 h-4 text-primary-400 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-white leading-relaxed">
              {generateInsight()}
            </p>
          </div>
          <div className="flex items-start gap-3">
            <Target className="w-4 h-4 text-primary-400 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-muted-foreground leading-relaxed">
              {getSecondaryInsight()}
            </p>
          </div>
        </div>

        {/* Supporting Metrics */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
          <div className="text-center">
            <div className={`text-lg font-bold ${
              oiDominance > 0 ? "text-success-400" : "text-danger-400"
            }`}>
              {(Math.abs(oiDominance) * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground">OI {oiDominance > 0 ? 'Put' : 'Call'} Dom</div>
          </div>
          <div className="text-center">
            <div className={`text-lg font-bold ${
              positionScore > 0 ? "text-success-400" : "text-danger-400"
            }`}>
              {(Math.abs(positionScore) * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground">Position</div>
          </div>
        </div>
      </div>
    </div>
  );
}
