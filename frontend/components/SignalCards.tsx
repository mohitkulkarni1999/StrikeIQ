import { RealTimeSignals } from '../types/market';
import { AlertCircle, TrendingUp, TrendingDown, Target } from 'lucide-react';

interface SignalCardsProps {
  signals: RealTimeSignals;
}

export default function SignalCards({ signals }: SignalCardsProps) {
  if (!signals) {
    return (
      <div className="glass-morphism rounded-xl p-6">
        <div className="text-center text-muted-foreground">
          <p>No signal data available</p>
        </div>
      </div>
    );
  }

  const { bias_signal, expected_move_signal, smart_money_signal, overall_signal } = signals || {
    bias_signal: { action: 'HOLD', strength: 'WEAK', confidence: 0 },
    expected_move_signal: { signal: 'NEUTRAL', action: 'HOLD', distance: 0 },
    smart_money_signal: { signal: 'NEUTRAL', action: 'HOLD', activities: [] },
    overall_signal: { action: 'HOLD', strength: 'WEAK', confidence: 0, reasoning: 'No signals available' }
  };

  const signalCards = [
    {
      title: 'Bias Signal',
      signal: bias_signal.action,
      strength: bias_signal.strength,
      confidence: bias_signal.confidence,
      icon: bias_signal.action === 'BUY' ? <TrendingUp className="w-6 h-6" /> : 
             bias_signal.action === 'SELL' ? <TrendingDown className="w-6 h-6" /> : 
             <Target className="w-6 h-6" />,
      color: bias_signal.action === 'BUY' ? 'success' : 
             bias_signal.action === 'SELL' ? 'danger' : 'warning',
      description: `Market bias indicates ${bias_signal.action.toLowerCase()} sentiment with ${bias_signal.strength.toLowerCase()} conviction.`
    },
    {
      title: 'Expected Move Signal',
      signal: expected_move_signal.signal,
      strength: expected_move_signal.action,
      confidence: (1 - expected_move_signal.distance) * 100,
      icon: expected_move_signal.signal === 'OVERBOUGHT' ? <TrendingUp className="w-6 h-6" /> : 
             expected_move_signal.signal === 'OVERSOLD' ? <TrendingDown className="w-6 h-6" /> : 
             <Target className="w-6 h-6" />,
      color: expected_move_signal.signal === 'OVERBOUGHT' ? 'danger' : 
             expected_move_signal.signal === 'OVERSOLD' ? 'success' : 'warning',
      description: `Price is in ${expected_move_signal.signal.toLowerCase()} zone. Consider ${expected_move_signal.action.toLowerCase()} position.`
    },
    {
      title: 'Smart Money Signal',
      signal: smart_money_signal.signal,
      strength: smart_money_signal.action,
      confidence: smart_money_signal.activities ? smart_money_signal.activities.length * 20 : 0,
      icon: smart_money_signal.signal.includes('BULLISH') ? <TrendingUp className="w-6 h-6" /> : 
             smart_money_signal.signal.includes('BEARISH') ? <TrendingDown className="w-6 h-6" /> : 
             <AlertCircle className="w-6 h-6" />,
      color: smart_money_signal.signal.includes('BULLISH') ? 'success' : 
             smart_money_signal.signal.includes('BEARISH') ? 'danger' : 'warning',
      description: `Institutional activity shows ${smart_money_signal.signal.toLowerCase().replace('_', ' ')} pattern.`
    },
    {
      title: 'Overall Signal',
      signal: overall_signal.action,
      strength: overall_signal.strength,
      confidence: overall_signal.confidence,
      icon: overall_signal.action === 'BUY' ? <TrendingUp className="w-6 h-6" /> : 
             overall_signal.action === 'SELL' ? <TrendingDown className="w-6 h-6" /> : 
             <Target className="w-6 h-6" />,
      color: overall_signal.action === 'BUY' ? 'success' : 
             overall_signal.action === 'SELL' ? 'danger' : 'warning',
      description: overall_signal.reasoning
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
          <div key={index} className="signal-card">
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
                  <span className="font-medium capitalize">{card.strength.toLowerCase()}</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
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
                <div className="w-full bg-muted rounded-full h-2">
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
