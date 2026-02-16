import React from 'react';
import { AlertCircle, TrendingUp, TrendingDown, Target } from 'lucide-react';

interface SignalCardsProps {
  intelligence?: {
    bias: {
      score: number;
      label: string;
      strength: number;
      direction: string;
      confidence: number;
      signal: string;
    };
    probability?: {
      expected_move: number;
      upper_1sd: number;
      lower_1sd: number;
      upper_2sd: number;
      lower_2sd: number;
      breach_probability: number;
      range_hold_probability: number;
      volatility_state: string;
    };
    liquidity: {
      total_oi: number;
      oi_change_24h: number;
      concentration: number;
      depth_score: number;
      flow_direction: string;
    };
  };
}

export default function SignalCards({ intelligence }: SignalCardsProps) {
  console.log('🔍 SignalCards - Received intelligence:', intelligence);
  
  if (!intelligence) {
    return (
      <div className="glass-morphism rounded-xl p-6 border border-white/10">
        <div className="text-center text-muted-foreground">
          <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>Signal data unavailable</p>
        </div>
      </div>
    );
  }

  const { bias, probability, liquidity } = intelligence;

  const signalCards = [
    {
      title: 'Bias Signal',
      signal: bias?.signal || 'NEUTRAL',
      strength: bias?.strength || 'UNKNOWN',
      confidence: bias?.confidence || 0,
      icon: bias?.label?.toUpperCase() === 'BULLISH' ? <TrendingUp className="w-6 h-6" /> : 
             bias?.label?.toUpperCase() === 'BEARISH' ? <TrendingDown className="w-6 h-6" /> : 
             <Target className="w-6 h-6" />,
      color: bias?.label?.toUpperCase() === 'BULLISH' ? 'success' : 
             bias?.label?.toUpperCase() === 'BEARISH' ? 'danger' : 'warning',
      description: `Market bias indicates ${bias?.label?.toString().toLowerCase() || 'neutral'} sentiment with ${bias?.strength?.toString().toLowerCase() || 'unknown'} conviction.`
    },
    {
      title: 'Expected Move Signal',
      signal: probability?.volatility_state?.toUpperCase() || 'NEUTRAL',
      strength: probability?.expected_move > 0 ? 'MODERATE' : 'WEAK',
      confidence: probability?.range_hold_probability || 0,
      icon: probability?.volatility_state === 'overpriced' ? <TrendingUp className="w-6 h-6" /> : 
             probability?.volatility_state === 'underpriced' ? <TrendingDown className="w-6 h-6" /> : 
             <Target className="w-6 h-6" />,
      color: probability?.volatility_state === 'overpriced' ? 'danger' : 
             probability?.volatility_state === 'underpriced' ? 'success' : 'warning',
      description: `Expected move of ±${probability?.expected_move?.toFixed(2) || '0.00'} indicates ${probability?.volatility_state || 'neutral'} pricing.`
    },
    {
      title: 'Liquidity Signal',
      signal: liquidity?.flow_direction?.toUpperCase() || 'NEUTRAL',
      strength: liquidity?.depth_score > 0.7 ? 'STRONG' : liquidity?.depth_score > 0.4 ? 'MODERATE' : 'WEAK',
      confidence: liquidity?.concentration ? (1 - liquidity.concentration) * 100 : 0,
      icon: liquidity?.flow_direction?.includes('BULLISH') ? <TrendingUp className="w-6 h-6" /> : 
             liquidity?.flow_direction?.includes('BEARISH') ? <TrendingDown className="w-6 h-6" /> : 
             <AlertCircle className="w-6 h-6" />,
      color: liquidity?.flow_direction?.includes('BULLISH') ? 'success' : 
             liquidity?.flow_direction?.includes('BEARISH') ? 'danger' : 'warning',
      description: `Liquidity depth score of ${(liquidity?.depth_score * 100).toFixed(1)}% with ${liquidity?.flow_direction?.toLowerCase() || 'neutral'} flow.`
    },
    {
      title: 'Overall Signal',
      signal: bias?.signal || 'NEUTRAL',
      strength: bias?.strength || 'UNKNOWN',
      confidence: bias?.confidence || 0,
      icon: bias?.label?.toUpperCase() === 'BULLISH' ? <TrendingUp className="w-6 h-6" /> : 
             bias?.label?.toUpperCase() === 'BEARISH' ? <TrendingDown className="w-6 h-6" /> : 
             <Target className="w-6 h-6" />,
      color: bias?.label?.toUpperCase() === 'BULLISH' ? 'success' : 
             bias?.label?.toUpperCase() === 'BEARISH' ? 'danger' : 'warning',
      description: `Overall market bias is ${bias?.label?.toLowerCase() || 'neutral'} with ${bias?.confidence?.toFixed(1) || '0.0'}% confidence.`
    }
  ];

  const getColorClasses = (color: string) => {
    const colorMap = {
      success: {
        bg: 'bg-success-500/20',
        border: 'border-success-500/30',
        text: 'text-success-500',
        iconBg: 'bg-success-500'
      },
      danger: {
        bg: 'bg-danger-500/20',
        border: 'border-danger-500/30',
        text: 'text-danger-500',
        iconBg: 'bg-danger-500'
      },
      warning: {
        bg: 'bg-warning-500/20',
        border: 'border-warning-500/30',
        text: 'text-warning-500',
        iconBg: 'bg-warning-500'
      }
    };
    return colorMap[color as keyof typeof colorMap] || colorMap.warning;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {signalCards.map((card, index) => {
        const colors = getColorClasses(card.color);
        
        return (
          <div key={index} className="glass-morphism rounded-xl p-6 border border-white/10">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-1">
                  {card.title}
                </h4>
                <div className={`text-lg font-bold ${colors.text}`}>
                  {card.signal}
                </div>
              </div>
              <div className={`p-2 rounded-lg ${colors.iconBg} text-white`}>
                {card.icon}
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-muted-foreground">Strength</span>
                  <span className="font-medium capitalize">{typeof card.strength === 'string' ? card.strength.toLowerCase() : card.strength.toString()}</span>
                </div>
                <div className="w-full bg-black/30 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      card.strength === 'STRONG' ? 'w-4/5' :
                      card.strength === 'MODERATE' ? 'w-1/2' : 'w-1/4'
                    } ${colors.iconBg}`}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-muted-foreground">Confidence</span>
                  <span className="font-medium">{card.confidence.toFixed(0)}%</span>
                </div>
                <div className="w-full bg-black/30 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${colors.iconBg}`}
                    style={{ width: `${Math.min(card.confidence, 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-white/10">
              <p className="text-xs text-muted-foreground leading-relaxed">
                {card.description}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
