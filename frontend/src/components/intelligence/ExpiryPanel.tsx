import React from 'react';
import { Calendar, Target, Magnet, AlertTriangle } from 'lucide-react';

interface ExpiryAnalysis {
  days_to_expiry: number;
  pin_probability: number;
  magnet_strength: number;
  max_oi_strike: number;
  max_gamma_strike: number;
  expiry_risk_level: 'critical' | 'high' | 'medium' | 'low';
  recommended_strategies: string[];
  summary: {
    pin_risk: string;
    magnet_strength_level: string;
    expiry_urgency: string;
  };
}

interface ExpiryPanelProps {
  expiryAnalysis: ExpiryAnalysis;
}

const ExpiryPanel: React.FC<ExpiryPanelProps> = ({ expiryAnalysis }) => {
  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'critical':
        return 'bg-red-500/20 border-red-500/40 text-red-400';
      case 'high':
        return 'bg-orange-500/20 border-orange-500/40 text-orange-400';
      case 'medium':
        return 'bg-yellow-500/20 border-yellow-500/40 text-yellow-400';
      case 'low':
        return 'bg-green-500/20 border-green-500/40 text-green-400';
      default:
        return 'bg-gray-500/20 border-gray-500/40 text-gray-400';
    }
  };

  const getRiskBadge = (level: string) => {
    const colors = {
      critical: 'bg-red-500 text-white',
      high: 'bg-orange-500 text-white',
      medium: 'bg-yellow-500 text-black',
      low: 'bg-green-500 text-white'
    };
    
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${colors[level as keyof typeof colors] || colors.low}`}>
        {level}
      </span>
    );
  };

  const getPinProbabilityColor = (probability: number) => {
    if (probability >= 80) return 'text-red-400';
    if (probability >= 60) return 'text-orange-400';
    if (probability >= 40) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getMagnetStrengthColor = (strength: number) => {
    if (strength >= 80) return 'text-purple-400';
    if (strength >= 60) return 'text-blue-400';
    if (strength >= 40) return 'text-cyan-400';
    return 'text-gray-400';
  };

  const formatDaysToExpiry = (days: number) => {
    if (days <= 0) return 'Expiry Day';
    if (days === 1) return '1 Day';
    if (days <= 7) return `${days} Days`;
    return `${days} Days`;
  };

  return (
    <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-white flex items-center">
          <Calendar className="w-5 h-5 mr-3 text-purple-400" />
          Expiry Intelligence
        </h3>
        
        {/* Risk Level Badge */}
        {getRiskBadge(expiryAnalysis.expiry_risk_level)}
      </div>

      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Days to Expiry */}
        <div className="text-center">
          <div className="text-sm text-gray-400 uppercase tracking-wide mb-2">
            Days to Expiry
          </div>
          <div className={`text-3xl font-bold ${
            expiryAnalysis.days_to_expiry <= 3 ? 'text-red-400' :
            expiryAnalysis.days_to_expiry <= 7 ? 'text-orange-400' :
            expiryAnalysis.days_to_expiry <= 15 ? 'text-yellow-400' :
            'text-green-400'
          }`}>
            {formatDaysToExpiry(expiryAnalysis.days_to_expiry)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {expiryAnalysis.summary.expiry_urgency?.replace('_', ' ') || 'Unknown'}
          </div>
        </div>

        {/* Pin Probability */}
        <div className="text-center">
          <div className="text-sm text-gray-400 uppercase tracking-wide mb-2">
            Pin Probability
          </div>
          <div className={`text-3xl font-bold ${getPinProbabilityColor(expiryAnalysis.pin_probability)}`}>
            {Math.round(expiryAnalysis.pin_probability)}%
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {expiryAnalysis.summary.pin_risk === 'high' ? 'High pin risk' :
             expiryAnalysis.summary.pin_risk === 'medium' ? 'Moderate pin risk' :
             expiryAnalysis.summary.pin_risk === 'low' ? 'Low pin risk' : 'Pin risk unknown'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Magnet Strength */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-gray-300">Magnet Strength</h4>
            <Magnet className="w-4 h-4 text-purple-400" />
          </div>
          
          <div className="flex items-center space-x-3">
            <div className={`text-xl font-bold ${getMagnetStrengthColor(expiryAnalysis.magnet_strength)}`}>
              {Math.round(expiryAnalysis.magnet_strength)}/100
            </div>
            
            {/* Magnet Strength Bar */}
            <div className="flex-1">
              <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                <div 
                  className={`h-full transition-all duration-500 ${
                    expiryAnalysis.magnet_strength >= 80 ? 'bg-purple-500' :
                    expiryAnalysis.magnet_strength >= 60 ? 'bg-blue-500' :
                    expiryAnalysis.magnet_strength >= 40 ? 'bg-cyan-500' : 'bg-gray-500'
                  }`}
                  style={{ width: `${expiryAnalysis.magnet_strength}%` }}
                />
              </div>
            </div>
          </div>
          
          <div className="text-xs text-gray-400 mt-2">
            {expiryAnalysis.summary.magnet_strength_level || 'Unknown'}
          </div>
        </div>

        {/* Key Strikes */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
          <h4 className="text-sm font-medium text-gray-300 mb-3">Key Strikes</h4>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-xs text-gray-400">Max OI Strike</div>
              <div className="font-mono font-semibold text-white">
                {Math.round(expiryAnalysis.max_oi_strike)}
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="text-xs text-gray-400">Max Gamma Strike</div>
              <div className="font-mono font-semibold text-white">
                {Math.round(expiryAnalysis.max_gamma_strike)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recommended Strategies */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-300 mb-3 flex items-center">
          <Target className="w-4 h-4 mr-2 text-green-400" />
          Recommended Strategies
        </h4>
        
        <div className="grid grid-cols-2 gap-2">
          {expiryAnalysis.recommended_strategies?.slice(0, 6).map((strategy, index) => (
            <div key={index} className="flex items-center space-x-2 p-2 bg-white/5 rounded-lg">
              <div className="w-2 h-2 bg-green-400 rounded-full" />
              <div className="text-sm text-white capitalize">
                {strategy.replace('_', ' ')}
              </div>
            </div>
          ))}
        </div>
        
        {expiryAnalysis.days_to_expiry <= 3 && (
          <div className="mt-3 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
            <div className="flex items-center text-red-400 text-sm font-medium">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Critical expiry period - Use extreme caution
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExpiryPanel;
