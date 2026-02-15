import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ConvictionPanelProps {
  conviction: number; // 0-100
  directionalPressure: number; // -100 to +100
  instabilityIndex: number; // 0-100
}

const ConvictionPanel: React.FC<ConvictionPanelProps> = ({
  conviction,
  directionalPressure,
  instabilityIndex
}) => {
  const getConvictionColor = (value: number) => {
    if (value >= 80) return 'bg-green-500';
    if (value >= 60) return 'bg-green-400';
    if (value >= 40) return 'bg-yellow-400';
    if (value >= 20) return 'bg-orange-400';
    return 'bg-red-400';
  };

  const getPressureColor = (value: number) => {
    if (value > 30) return 'bg-green-500';
    if (value < -30) return 'bg-red-500';
    return 'bg-gray-500';
  };

  const getInstabilityColor = (value: number) => {
    if (value >= 70) return 'bg-red-500';
    if (value >= 50) return 'bg-orange-400';
    if (value >= 30) return 'bg-yellow-400';
    return 'bg-green-400';
  };

  const getPressureIcon = (value: number) => {
    if (value > 30) return <TrendingUp className="w-5 h-5" />;
    if (value < -30) return <TrendingDown className="w-5 h-5" />;
    return <Minus className="w-5 h-5" />;
  };

  return (
    <div className="grid grid-cols-3 gap-4 mb-6">
      {/* Structural Conviction Card */}
      <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-300">Structural Conviction</h3>
          <div className="text-xs text-gray-500 uppercase tracking-wide">0-100</div>
        </div>
        
        <div className="relative">
          <div className="w-full bg-gray-800 rounded-full h-4 overflow-hidden">
            <div 
              className={`h-full transition-all duration-700 ease-out ${getConvictionColor(conviction)}`}
              style={{ width: `${conviction}%` }}
            />
          </div>
        </div>
        
        <div className="mt-3 text-2xl font-bold text-white">
          {Math.round(conviction)}
        </div>
      </div>

      {/* Directional Pressure Card */}
      <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-300">Directional Pressure</h3>
          <div className="flex items-center space-x-2">
            {getPressureIcon(directionalPressure)}
            <div className="text-xs text-gray-500 uppercase tracking-wide">-100/+100</div>
          </div>
        </div>
        
        <div className="relative">
          <div className="w-full bg-gray-800 rounded-full h-4 overflow-hidden relative">
            {/* Center line */}
            <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-gray-600 transform -translate-x-1/2" />
            
            {/* Pressure bar */}
            <div 
              className={`h-full transition-all duration-700 ease-out ${getPressureColor(directionalPressure)}`}
              style={{ 
                width: `${Math.abs(directionalPressure)}%`,
                marginLeft: directionalPressure >= 0 ? '50%' : `${50 - Math.abs(directionalPressure)}%`
              }}
            />
          </div>
        </div>
        
        <div className="mt-3 text-2xl font-bold text-white text-center">
          {directionalPressure > 0 ? '+' : ''}{Math.round(directionalPressure)}
        </div>
      </div>

      {/* Instability Index Card */}
      <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-300">Instability Index</h3>
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${
            instabilityIndex > 70 
              ? 'bg-red-500/20 text-red-400 border border-red-500/30' 
              : 'bg-gray-800 text-gray-400'
          }`}>
            {instabilityIndex > 70 ? 'HIGH' : 'NORMAL'}
          </div>
        </div>
        
        <div className="relative">
          <div className="w-full bg-gray-800 rounded-full h-4 overflow-hidden">
            <div 
              className={`h-full transition-all duration-700 ease-out ${getInstabilityColor(instabilityIndex)}`}
              style={{ width: `${instabilityIndex}%` }}
            />
          </div>
        </div>
        
        <div className="mt-3 text-2xl font-bold text-white text-center">
          {Math.round(instabilityIndex)}
        </div>
      </div>
    </div>
  );
};

export default ConvictionPanel;
