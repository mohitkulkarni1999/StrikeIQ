import React, { useEffect, useState } from 'react';
import { AlertTriangle, TrendingUp, Activity, Target } from 'lucide-react';

interface StructuralBannerProps {
  regime: string;
  confidence: number;
  stability: number;
  acceleration: number;
  onRegimeChange?: (regime: string) => void;
}

const StructuralBanner: React.FC<StructuralBannerProps> = ({
  regime,
  confidence,
  stability,
  acceleration,
  onRegimeChange
}) => {
  const [previousRegime, setPreviousRegime] = useState(regime);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (previousRegime !== regime) {
      setIsAnimating(true);
      setPreviousRegime(regime);
      setTimeout(() => setIsAnimating(false), 1000);
      onRegimeChange?.(regime);
    }
  }, [regime, previousRegime, onRegimeChange]);

  const getRegimeColor = (regime: string) => {
    switch (regime?.toLowerCase()) {
      case 'range':
        return 'from-green-500/20 to-green-600/20 border-green-500/30 text-green-400';
      case 'trend':
        return 'from-red-500/20 to-red-600/20 border-red-500/30 text-red-400';
      case 'breakout':
        return 'from-yellow-500/20 to-yellow-600/20 border-yellow-500/30 text-yellow-400';
      case 'pin_risk':
        return 'from-blue-500/20 to-blue-600/20 border-blue-500/30 text-blue-400';
      default:
        return 'from-gray-500/20 to-gray-600/20 border-gray-500/30 text-gray-400';
    }
  };

  const getRegimeIcon = (regime: string) => {
    switch (regime?.toLowerCase()) {
      case 'range':
        return <Activity className="w-6 h-6" />;
      case 'trend':
        return <TrendingUp className="w-6 h-6" />;
      case 'breakout':
        return <Target className="w-6 h-6" />;
      case 'pin_risk':
        return <AlertTriangle className="w-6 h-6" />;
      default:
        return <Activity className="w-6 h-6" />;
    }
  };

  const getAccelerationColor = (acceleration: number) => {
    if (acceleration > 20) return 'text-green-400';
    if (acceleration < -20) return 'text-red-400';
    return 'text-gray-400';
  };

  const getStabilityColor = (stability: number) => {
    if (stability >= 80) return 'text-green-400';
    if (stability >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className={`
      w-full bg-gradient-to-r ${getRegimeColor(regime)} 
      border rounded-2xl p-6 backdrop-blur-sm
      transition-all duration-500 ease-in-out
      ${isAnimating ? 'animate-pulse' : ''}
    `}>
      <div className="flex items-center justify-between">
        {/* Left: Regime Display */}
        <div className="flex items-center space-x-4">
          <div className={`p-3 rounded-xl bg-black/20 backdrop-blur-sm`}>
            {getRegimeIcon(regime)}
          </div>
          <div>
            <div className="text-3xl font-bold tracking-tight">
              {regime?.replace('_', ' ').toUpperCase() || 'UNKNOWN'}
            </div>
            <div className="text-sm opacity-70 mt-1">
              Structural Regime
            </div>
          </div>
        </div>

        {/* Right: Metrics */}
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
