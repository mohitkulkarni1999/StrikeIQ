import React from 'react';
import { GitBranch, TrendingUp, Shield, Target } from 'lucide-react';

interface FlowGammaInteraction {
  interaction_type: string;
  confidence: number;
  description: string;
  summary: {
    primary_strategy: string;
    direction: string;
    risk_level: string;
    opportunity_score: number;
  };
  trading_implications: {
    strategy: string;
    direction: string;
    volatility: string;
    timeframe: string;
    key_levels: string;
  };
  opportunities: {
    [key: string]: boolean;
  };
}

interface InteractionPanelProps {
  interaction: FlowGammaInteraction;
}

const InteractionPanel: React.FC<InteractionPanelProps> = ({ interaction }) => {
  const getInteractionIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'range_compression':
        return <GitBranch className="w-5 h-5" />;
      case 'downside_acceleration':
        return <TrendingUp className="w-5 h-5 rotate-180" />;
      case 'upside_breakout_risk':
        return <Target className="w-5 h-5" />;
      case 'momentum_build':
        return <TrendingUp className="w-5 h-5" />;
      default:
        return <Shield className="w-5 h-5" />;
    }
  };

  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'high':
        return 'bg-red-500/20 border-red-500/40 text-red-400';
      case 'medium':
        return 'bg-yellow-500/20 border-yellow-500/40 text-yellow-400';
      case 'low':
        return 'bg-green-500/20 border-green-500/40 text-green-400';
      default:
        return 'bg-gray-500/20 border-gray-500/40 text-gray-400';
    }
  };

  const getOpportunityColor = (score: number) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    if (score >= 40) return 'text-orange-400';
    return 'text-red-400';
  };

  const formatInteractionType = (type: string) => {
    return type?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Unknown';
  };

  const getStrategyDescription = (strategy: string) => {
    const descriptions: { [key: string]: string } = {
      'range_bound': 'Price likely to stay within defined range',
      'bearish': 'Downward pressure with increasing volatility',
      'bullish_breakout': 'Potential upward price breakout',
      'momentum': 'Strong directional movement expected',
      'mean_reversion': 'Price likely to revert to mean',
      'volatility': 'High volatility expansion expected',
      'cautious': 'Reduce position size, wait for clarity'
    };
    return descriptions[strategy] || 'Monitor market conditions';
  };

  return (
    <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-white">Flow + Gamma Interaction</h3>
        
        {/* Confidence Badge */}
        <div className="flex items-center space-x-2">
          <div className="text-sm text-gray-400">Confidence</div>
          <div className="px-3 py-1 bg-blue-500/20 border border-blue-500/40 rounded-full">
            <span className="text-blue-400 font-medium">{Math.round(interaction.confidence)}%</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Left: Interaction Summary */}
        <div>
          <div className="mb-6">
            <div className="flex items-center space-x-3 mb-3">
              <div className="p-2 bg-white/10 rounded-lg">
                {getInteractionIcon(interaction.interaction_type)}
              </div>
              <div>
                <div className="text-lg font-semibold text-white">
                  {formatInteractionType(interaction.interaction_type)}
                </div>
                <div className="text-sm text-gray-400">
                  Structural Interaction
                </div>
              </div>
            </div>
            
            <div className="text-sm text-gray-300 leading-relaxed">
              {interaction.description}
            </div>
          </div>

          {/* Strategy Guidance Box */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
            <h4 className="text-sm font-medium text-gray-300 uppercase tracking-wide mb-3">
              Strategy Guidance
            </h4>
            
            <div className="space-y-3">
              <div>
                <div className="text-xs text-gray-500 uppercase">Primary Strategy</div>
                <div className="text-white font-medium">
                  {interaction.summary.primary_strategy?.replace('_', ' ') || 'Unknown'}
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {getStrategyDescription(interaction.summary.primary_strategy)}
                </div>
              </div>

              <div>
                <div className="text-xs text-gray-500 uppercase">Direction</div>
                <div className="text-white font-medium capitalize">
                  {interaction.summary.direction || 'Unknown'}
                </div>
              </div>

              <div>
                <div className="text-xs text-gray-500 uppercase">Timeframe</div>
                <div className="text-white font-medium capitalize">
                  {interaction.trading_implications.timeframe?.replace('_', ' ') || 'Unknown'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Risk & Opportunity Analysis */}
        <div>
          {/* Risk Level */}
          <div className={`p-4 rounded-xl border mb-4 ${getRiskColor(interaction.summary.risk_level)}`}>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium uppercase tracking-wide">Risk Level</h4>
              <div className="px-2 py-1 bg-black/30 rounded text-xs font-medium">
                {interaction.summary.risk_level?.toUpperCase() || 'UNKNOWN'}
              </div>
            </div>
            
            <div className="text-sm leading-relaxed">
              {interaction.summary.risk_level === 'high' && 'High risk conditions detected. Use tight stops.'}
              {interaction.summary.risk_level === 'medium' && 'Moderate risk. Monitor key levels closely.'}
              {interaction.summary.risk_level === 'low' && 'Lower risk environment. Standard position sizing.'}
              {!interaction.summary.risk_level && 'Risk assessment unavailable.'}
            </div>
          </div>

          {/* Opportunity Score */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 mb-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-gray-300 uppercase tracking-wide">
                Opportunity Score
              </h4>
              <div className={`text-lg font-bold ${getOpportunityColor(interaction.summary.opportunity_score)}`}>
                {Math.round(interaction.summary.opportunity_score)}/100
              </div>
            </div>
            
            <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
              <div 
                className={`h-full transition-all duration-500 ${
                  interaction.summary.opportunity_score >= 80 ? 'bg-green-500' :
                  interaction.summary.opportunity_score >= 60 ? 'bg-yellow-500' :
                  interaction.summary.opportunity_score >= 40 ? 'bg-orange-500' : 'bg-red-500'
                }`}
                style={{ width: `${interaction.summary.opportunity_score}%` }}
              />
            </div>
          </div>

          {/* Trading Opportunities */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
            <h4 className="text-sm font-medium text-gray-300 uppercase tracking-wide mb-3">
              Trading Opportunities
            </h4>
            
            <div className="space-y-2">
              {Object.entries(interaction.opportunities || {}).map(([opportunity, available]) => (
                <div key={opportunity} className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${
                    available ? 'bg-green-400' : 'bg-gray-600'
                  }`} />
                  <div className={`text-sm capitalize ${
                    available ? 'text-white' : 'text-gray-500'
                  }`}>
                    {opportunity.replace('_', ' ')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InteractionPanel;
