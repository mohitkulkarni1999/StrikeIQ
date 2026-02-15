import React from 'react';
import { Magnet, ArrowDownRight, TrendingUp } from 'lucide-react';

interface GammaPressurePoint {
  strike: number;
  strength: number;
  distance_from_spot: number;
  net_gex: number;
}

interface GammaPressureMap {
  strongest_magnet?: {
    strike: number;
    message: string;
  };
  strongest_cliff?: {
    strike: number;
    message: string;
  };
  top_magnets: GammaPressurePoint[];
  top_cliffs: GammaPressurePoint[];
  gamma_flip_level?: number;
  distance_from_flip?: number;
}

interface GammaPressurePanelProps {
  pressureMap: GammaPressureMap;
  spot: number;
}

const GammaPressurePanel: React.FC<GammaPressurePanelProps> = ({ pressureMap, spot }) => {
  const getHeatColor = (strength: number) => {
    if (strength >= 80) return 'bg-red-500/20 border-red-500/40 text-red-400';
    if (strength >= 60) return 'bg-orange-500/20 border-orange-500/40 text-orange-400';
    if (strength >= 40) return 'bg-yellow-500/20 border-yellow-500/40 text-yellow-400';
    if (strength >= 20) return 'bg-blue-500/20 border-blue-500/40 text-blue-400';
    return 'bg-gray-500/20 border-gray-500/40 text-gray-400';
  };

  const getStrengthBar = (strength: number) => {
    return (
      <div className="w-16 bg-gray-800 rounded-full h-2 overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-blue-500 to-red-500 transition-all duration-500"
          style={{ width: `${strength}%` }}
        />
      </div>
    );
  };

  return (
    <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-white flex items-center">
          <Magnet className="w-5 h-5 mr-3 text-blue-400" />
          Gamma Pressure Map
        </h3>
        
        {/* Flip Level Info */}
        {pressureMap.gamma_flip_level && (
          <div className="text-right">
            <div className="text-sm text-gray-400">Flip Level</div>
            <div className="text-lg font-mono font-bold text-white">
              {Math.round(pressureMap.gamma_flip_level)}
            </div>
            <div className="text-xs text-gray-500">
              {Math.round(pressureMap.distance_from_flip || 0)} pts away
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Top Magnets */}
        <div>
          <h4 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-4 flex items-center">
            <TrendingUp className="w-4 h-4 mr-2 text-green-400" />
            Top 5 Gamma Magnets
          </h4>
          
          <div className="space-y-2">
            {pressureMap.top_magnets?.slice(0, 5).map((magnet, index) => (
              <div 
                key={`magnet-${index}`}
                className={`
                  flex items-center justify-between p-3 rounded-lg border
                  ${magnet.strike === spot ? 'bg-white/5 border-white/20' : ''}
                  ${getHeatColor(magnet.strength)}
                `}
              >
                <div className="flex items-center space-x-3">
                  <div className="text-xs text-gray-500 w-4">
                    {index + 1}
                  </div>
                  <div>
                    <div className="font-mono font-semibold text-white">
                      {Math.round(magnet.strike)}
                    </div>
                    <div className="text-xs text-gray-400">
                      {Math.round(magnet.distance_from_spot)} pts
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {getStrengthBar(magnet.strength)}
                  <div className="text-xs text-gray-400 w-8 text-right">
                    {Math.round(magnet.strength)}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Strongest Magnet Highlight */}
          {pressureMap.strongest_magnet && (
            <div className="mt-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <div className="flex items-center text-green-400 text-sm font-medium">
                <Magnet className="w-4 h-4 mr-2" />
                {pressureMap.strongest_magnet.message}
              </div>
            </div>
          )}
        </div>

        {/* Top Cliffs */}
        <div>
          <h4 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-4 flex items-center">
            <ArrowDownRight className="w-4 h-4 mr-2 text-red-400" />
            Top 5 Gamma Cliffs
          </h4>
          
          <div className="space-y-2">
            {pressureMap.top_cliffs?.slice(0, 5).map((cliff, index) => (
              <div 
                key={`cliff-${index}`}
                className={`
                  flex items-center justify-between p-3 rounded-lg border
                  ${cliff.strike === spot ? 'bg-white/5 border-white/20' : ''}
                  ${getHeatColor(cliff.strength)}
                `}
              >
                <div className="flex items-center space-x-3">
                  <div className="text-xs text-gray-500 w-4">
                    {index + 1}
                  </div>
                  <div>
                    <div className="font-mono font-semibold text-white">
                      {Math.round(cliff.strike)}
                    </div>
                    <div className="text-xs text-gray-400">
                      {Math.round(cliff.distance_from_spot)} pts
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {getStrengthBar(cliff.strength)}
                  <div className="text-xs text-gray-400 w-8 text-right">
                    {Math.round(cliff.strength)}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Strongest Cliff Highlight */}
          {pressureMap.strongest_cliff && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
              <div className="flex items-center text-red-400 text-sm font-medium">
                <ArrowDownRight className="w-4 h-4 mr-2" />
                {pressureMap.strongest_cliff.message}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GammaPressurePanel;
