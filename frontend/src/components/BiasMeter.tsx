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
  console.log("BiasMeter received confidence:", intelligence?.bias?.confidence);

  if (!intelligence || !intelligence.bias) {
    return (
      <div className="bg-[#111827] rounded-xl p-5 border border-[#1F2937]">
        <div className="flex items-center gap-3 mb-4">
          <Target className="w-5 h-5 text-[#4F8CFF]" />
          <h3 className="text-lg font-semibold text-white">Market Bias</h3>
        </div>
        <div className="text-center text-gray-500 py-10">
          <div className="w-10 h-10 border-2 border-gray-700 border-t-gray-500 rounded-full animate-spin mx-auto mb-2" />
          <p>Bias data loading...</p>
        </div>
      </div>
    );
  }

  const { bias } = intelligence;
  const { score, label, strength, confidence, signal, direction } = bias;

  const getBiasColor = (label: string) => {
    if (label === null || label === undefined) return 'bg-[#FFC857]/20 text-[#FFC857]';
    switch (label.toUpperCase()) {
      case 'BULLISH':
        return 'bg-[#00FF9F]/20 text-[#00FF9F] border-[#00FF9F]/30';
      case 'BEARISH':
        return 'bg-[#FF4D4F]/20 text-[#FF4D4F] border-[#FF4D4F]/30';
      default:
        return 'bg-[#FFC857]/20 text-[#FFC857] border-[#FFC857]/30';
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
    if (confidence === null || confidence === undefined) return 'text-[#FFC857]';
    if (confidence >= 70) return 'text-[#00FF9F]';
    if (confidence >= 50) return 'text-[#FFC857]';
    return 'text-[#FF4D4F]';
  };

  const biasColor = getBiasColor(label);
  const biasIcon = getBiasIcon(label);
  const confidenceColor = getConfidenceColor(confidence);

  return (
    <div className="bg-[#111827] rounded-xl p-6 border border-[#1F2937]">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Target className="w-5 h-5 text-[#4F8CFF]" />
          <h3 className="text-lg font-semibold text-white">Market Bias</h3>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-[#00FF9F] rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-400">Live</span>
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
          <div className="text-sm text-gray-500 capitalize">
            {strength || 'unknown'} signal
          </div>
        </div>
      </div>

      {/* Confidence Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Confidence Level</span>
          <span className={confidenceColor}>
            {confidence !== null && confidence !== undefined ? confidence.toFixed(1) : '0.0'}%
          </span>
        </div>
        <div className="w-full bg-black/30 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-500 ${confidence !== null && confidence !== undefined && confidence >= 70
                ? 'bg-[#00FF9F]'
                : confidence !== null && confidence !== undefined && confidence >= 50
                  ? 'bg-[#FFC857]'
                  : 'bg-[#FF4D4F]'
              }`}
            style={{ width: `${confidence || 0}%` }}
          ></div>
        </div>
      </div>

      {/* Bias Components */}
      <div className="mt-6 pt-6 border-t border-[#1F2937]">
        <h4 className="text-sm font-medium text-gray-400 mb-3">Signal Components</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Bias Score</span>
            <span className="font-medium text-gray-200">{score !== null && score !== undefined ? score.toFixed(1) : '0.0'}/100</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Signal</span>
            <span className="font-medium text-gray-200">{signal || 'NEUTRAL'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Direction</span>
            <span className="font-medium text-gray-200 capitalize">{direction || 'neutral'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Strength</span>
            <span className="font-medium text-gray-200 capitalize">{strength || 'unknown'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
