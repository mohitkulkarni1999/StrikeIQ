import React from 'react';
import { TrendingUp, TrendingDown, Target, Activity } from 'lucide-react';

interface BiasMeterProps {
  intelligence?: {
    bias: {
      score: number;
      label: string;
      strength: number;
      direction: string;
      confidence: number;
      signal: string;
    };
  };
}

export default function BiasMeter({ intelligence }: BiasMeterProps) {
  console.log('🔍 BiasMeter - Received intelligence:', intelligence);
  
  if (!intelligence || !intelligence.bias) {
    return (
      <div className="glass-morphism rounded-2xl p-6 border border-white/10">
        <div className="flex items-center gap-3 mb-4">
          <Target className="w-5 h-5 text-primary-400" />
          <h3 className="text-lg font-semibold text-white">Market Bias</h3>
        </div>
        <div className="text-center text-muted-foreground">
          <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>Bias data unavailable</p>
        </div>
      </div>
    );
  }

  const { bias } = intelligence;
  const { score, label, strength, confidence, signal, direction } = bias;

  const getBiasColor = (label: string) => {
    if (label === null || label === undefined) return 'bg-warning-500/20 text-warning-500';
    switch (label.toUpperCase()) {
      case 'BULLISH':
        return 'bg-success-500/20 text-success-500 border-success-500/30';
      case 'BEARISH':
        return 'bg-danger-500/20 text-danger-500 border-danger-500/30';
      default:
        return 'bg-warning-500/20 text-warning-500 border-warning-500/30';
    }
  };

  const getBiasIcon = (label: string) => {
    if (label === null || label === undefined) return <Target className="w-6 h-6" />;
    switch (label.toUpperCase()) {
      case 'BULLISH':
        return <TrendingUp className="w-6 h-6" />;
      case 'BEARISH':
        return <TrendingDown className="w-6 h-6" />;
      default:
        return <Target className="w-6 h-6" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence === null || confidence === undefined) return 'text-warning-500';
    if (confidence >= 70) return 'text-success-500';
    if (confidence >= 50) return 'text-warning-500';
    return 'text-danger-500';
  };

  const biasColor = getBiasColor(label);
  const biasIcon = getBiasIcon(label);
  const confidenceColor = getConfidenceColor(confidence);

  return (
    <div className="glass-morphism rounded-2xl p-6 border border-white/10">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Target className="w-5 h-5 text-primary-400" />
          <h3 className="text-lg font-semibold text-white">Market Bias</h3>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-muted-foreground">Live</span>
        </div>
      </div>

      {/* Bias Meter Circle */}
      <div className="flex flex-col items-center mb-6">
        <div className={`w-32 h-32 rounded-full flex items-center justify-center text-white ${biasColor} shadow-lg transition-all duration-500`}>
          {biasIcon}
        </div>
        
        <div className="mt-4 text-center">
          <div className="text-2xl font-bold mb-1">{label || 'NEUTRAL'}</div>
          <div className={`text-lg font-medium ${confidenceColor}`}>
            {confidence !== null && confidence !== undefined ? confidence.toFixed(1) : '0.0'}% Confidence
          </div>
          <div className="text-sm text-muted-foreground capitalize">
            {strength || 'unknown'} signal
          </div>
        </div>
      </div>

      {/* Confidence Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Confidence Level</span>
          <span className={confidenceColor}>
            {confidence !== null && confidence !== undefined ? confidence.toFixed(1) : '0.0'}%
          </span>
        </div>
        <div className="w-full bg-black/30 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-500 ${
              confidence !== null && confidence !== undefined && confidence >= 70
                ? 'bg-success-500'
                : confidence !== null && confidence !== undefined && confidence >= 50
                ? 'bg-warning-500'
                : 'bg-danger-500'
            }`}
            style={{ width: `${confidence || 0}%` }}
          ></div>
        </div>
      </div>

      {/* Bias Components */}
      <div className="mt-6 pt-6 border-t border-white/10">
        <h4 className="text-sm font-medium text-muted-foreground mb-3">Signal Components</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Bias Score</span>
            <span className="font-medium">{score !== null && score !== undefined ? score.toFixed(1) : '0.0'}/100</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Signal</span>
            <span className="font-medium">{signal || 'NEUTRAL'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Direction</span>
            <span className="font-medium capitalize">{direction || 'neutral'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Strength</span>
            <span className="font-medium capitalize">{strength || 'unknown'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
