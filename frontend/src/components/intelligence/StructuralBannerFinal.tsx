import React, { useEffect, useState } from 'react';
import { Activity, TrendingUp, Target, AlertTriangle } from 'lucide-react';

interface StructuralBannerProps {
  regime: string;
  confidence: number;
  stability: number;
  acceleration: number;
}

const StructuralBanner: React.FC<StructuralBannerProps> = ({
  regime,
  confidence,
  stability,
  acceleration
}) => {
  const [isAnimating, setIsAnimating] = useState(false);
  const [currentRegime, setCurrentRegime] = useState(regime);

  useEffect(() => {
    if (currentRegime !== regime) {
      setIsAnimating(true);
      setCurrentRegime(regime);
      setTimeout(() => setIsAnimating(false), 1000);
    }
  }, [regime, currentRegime]);

  const getRegimeConfig = (regimeType: string) => {
    switch (regimeType?.toLowerCase()) {
      case 'range':
        return {
          color: 'from-green-500/20 to-green-600/20 border-green-500/30 text-green-400',
          glow: 'shadow-green-500/20',
          icon: <Activity className="w-6 h-6" />
        };
      case 'trend':
        return {
          color: 'from-red-500/20 to-red-600/20 border-red-500/30 text-red-400',
          glow: 'shadow-red-500/20',
          icon: <TrendingUp className="w-6 h-6" />
        };
      case 'breakout':
        return {
          color: 'from-yellow-500/20 to-yellow-600/20 border-yellow-500/30 text-yellow-400',
          glow: 'shadow-yellow-500/20',
          icon: <Target className="w-6 h-6" />
        };
      case 'pin_risk':
        return {
          color: 'from-blue-500/20 to-blue-600/20 border-blue-500/30 text-blue-400',
          glow: 'shadow-blue-500/20',
          icon: <AlertTriangle className="w-6 h-6" />
        };
      default:
        return {
          color: 'from-gray-500/20 to-gray-600/20 border-gray-500/30 text-gray-400',
          glow: 'shadow-gray-500/20',
          icon: <Activity className="w-6 h-6" />
        };
    }
  };

  const getAccelerationColor = (value: number) => {
    if (value > 20) return 'text-green-400';
    if (value < -20) return 'text-red-400';
    return 'text-gray-400';
  };

  const getStabilityColor = (value: number) => {
    if (value >= 80) return 'text-green-400';
    if (value >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const config = getRegimeConfig(currentRegime);

  return (
    <div className={`
      w-full bg-gradient-to-r ${config.color} 
      border rounded-2xl p-6 backdrop-blur-sm
      transition-all duration-500 ease-in-out
      ${isAnimating ? 'animate-pulse' : ''}
      shadow-lg ${config.glow}
    `}>
      <div className="flex items-center justify-between">
        {/* Regime Display */}
        <div className="flex items-center space-x-4">
          <div className="p-3 rounded-xl bg-black/20 backdrop-blur-sm">
            {config.icon}
          </div>
          <div>
            <div className="text-3xl font-bold tracking-tight">
              {currentRegime?.replace('_', ' ').toUpperCase() || 'UNKNOWN'}
            </div>
            <div className="text-sm opacity-70">
              Structural Regime
            </div>
          </div>
        </div>

        {/* Metrics */}
        <div className="flex items-center space-x-8">
          {/* Confidence */}
          <div className="text-center">
            <div className="text-2xl font-semibold">
              {Math.round(confidence)}%
            </div>
            <div className="text-xs opacity-70 uppercase tracking-wide">
              Confidence
            </div>
          </div>

          {/* Stability */}
          <div className="text-center">
            <div className={`text-2xl font-semibold ${getStabilityColor(stability)}`}>
              {Math.round(stability)}%
            </div>
            <div className="text-xs opacity-70 uppercase tracking-wide">
              Stability
            </div>
          </div>

          {/* Acceleration */}
          <div className="text-center">
            <div className={`text-2xl font-semibold ${getAccelerationColor(acceleration)}`}>
              {acceleration > 0 ? '+' : ''}{Math.round(acceleration)}
            </div>
            <div className="text-xs opacity-70 uppercase tracking-wide">
              Acceleration
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StructuralBanner;
