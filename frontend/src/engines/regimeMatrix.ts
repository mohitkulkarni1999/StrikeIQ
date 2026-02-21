import { MarketIntelligence } from './intelligenceEngine';

// Market regime classifications
export type MarketDirection = 'bullish' | 'bearish' | 'neutral';
export type VolatilityLevel = 'low' | 'normal' | 'elevated' | 'extreme';
export type LiquidityFlow = 'expanding' | 'contracting' | 'stable';

export interface MarketRegime {
  direction: MarketDirection;
  volatility: VolatilityLevel;
  liquidity: LiquidityFlow;
  classification: RegimeClassification;
  confidence: number;
  interpretation: string;
  trading_implications: string[];
}

export type RegimeClassification = 
  | 'BULLISH_EXPANSION'
  | 'BULLISH_COMPRESSION' 
  | 'BEARISH_DISTRIBUTION'
  | 'BEARISH_ACCUMULATION'
  | 'NEUTRAL_TRANSITION'
  | 'VOLATILITY_BREAKOUT'
  | 'LIQUIDITY_CRUNCH'
  | 'STABLE_GROWTH';

export class RegimeMatrix {
  
  static classifyMarketDirection(biasScore: number, biasLabel: string): MarketDirection {
    if (biasLabel.includes('BULL')) return 'bullish';
    if (biasLabel.includes('BEAR')) return 'bearish';
    return 'neutral';
  }

  static classifyLiquidityFlow(oiDominance: number, totalOI: number): LiquidityFlow {
    // Placeholder logic - would use actual OI flow data
    if (Math.abs(oiDominance) > 0.3) return oiDominance > 0 ? 'contracting' : 'expanding';
    return 'stable';
  }

  static computeRegime(intelligence: MarketIntelligence, oiDominance: number = 0): MarketRegime {
    const direction = this.classifyMarketDirection(intelligence.bias.score, intelligence.bias.label);
    const volatility = intelligence.volatility.current;
    const liquidity = this.classifyLiquidityFlow(oiDominance, intelligence.liquidity.total_oi);

    // Regime classification logic
    let classification: RegimeClassification;
    let interpretation: string;
    let trading_implications: string[];

    if (direction === 'bullish' && volatility === 'low' && liquidity === 'expanding') {
      classification = 'BULLISH_EXPANSION';
      interpretation = 'Controlled bullish accumulation with low volatility risk';
      trading_implications = [
        'Favorable for long positions',
        'Low risk of sudden reversals',
        'Good for entry scaling'
      ];
    } else if (direction === 'bullish' && volatility === 'extreme') {
      classification = 'VOLATILITY_BREAKOUT';
      interpretation = 'High volatility breakout with bullish bias';
      trading_implications = [
        'High risk/reward environment',
        'Potential for short squeeze',
        'Requires tight risk management'
      ];
    } else if (direction === 'bearish' && volatility === 'elevated' && liquidity === 'contracting') {
      classification = 'BEARISH_DISTRIBUTION';
      interpretation = 'Active distribution with elevated volatility';
      trading_implications = [
        'High risk environment',
        'Favorable for short positions',
        'Avoid bottom fishing'
      ];
    } else if (direction === 'bearish' && volatility === 'low') {
      classification = 'BEARISH_ACCUMULATION';
      interpretation = 'Quiet bearish phase - potential accumulation';
      trading_implications = [
        'Wait for confirmation',
        'Monitor for reversal signals',
        'Reduced position sizes'
      ];
    } else if (direction === 'neutral' && volatility === 'elevated') {
      classification = 'NEUTRAL_TRANSITION';
      interpretation = 'High volatility transition phase';
      trading_implications = [
        'Wait for direction clarity',
        'Increased whipsaw risk',
        'Focus on range-bound strategies'
      ];
    } else if (liquidity === 'expanding' && volatility === 'normal') {
      classification = 'STABLE_GROWTH';
      interpretation = 'Stable market with expanding liquidity';
      trading_implications = [
        'Favorable environment',
        'Trend-following strategies work',
        'Moderate risk levels'
      ];
    } else if (volatility === 'extreme' && liquidity === 'contracting') {
      classification = 'LIQUIDITY_CRUNCH';
      interpretation = 'Liquidity withdrawal with extreme volatility';
      trading_implications = [
        'Very high risk environment',
        'Preserve capital',
        'Consider market exit'
      ];
    } else {
      classification = 'BULLISH_COMPRESSION';
      interpretation = 'Bullish bias in compression phase';
      trading_implications = [
        'Monitor for breakout',
        'Build positions gradually',
        'Watch volume confirmation'
      ];
    }

    // Calculate overall confidence
    const confidence = (intelligence.confidence + intelligence.bias.confidence) / 2;

    return {
      direction,
      volatility,
      liquidity,
      classification,
      confidence,
      interpretation,
      trading_implications
    };
  }

  static getRegimeColor(regime: RegimeClassification): string {
    switch (regime) {
      case 'BULLISH_EXPANSION':
      case 'STABLE_GROWTH':
        return 'text-success-400 border-success-500/30 bg-success-500/10';
      case 'BULLISH_COMPRESSION':
        return 'text-blue-400 border-blue-500/30 bg-blue-500/10';
      case 'BEARISH_DISTRIBUTION':
      case 'LIQUIDITY_CRUNCH':
        return 'text-danger-400 border-danger-500/30 bg-danger-500/10';
      case 'BEARISH_ACCUMULATION':
        return 'text-warning-400 border-warning-500/30 bg-warning-500/10';
      case 'VOLATILITY_BREAKOUT':
        return 'text-analytics-400 border-analytics-500/30 bg-analytics-500/10';
      case 'NEUTRAL_TRANSITION':
      default:
        return 'text-muted-foreground border-muted-foreground/30 bg-muted-foreground/10';
    }
  }

  static getRegimeIcon(regime: RegimeClassification): string {
    switch (regime) {
      case 'BULLISH_EXPANSION':
      case 'STABLE_GROWTH':
        return '📈';
      case 'BULLISH_COMPRESSION':
        return '📊';
      case 'BEARISH_DISTRIBUTION':
      case 'LIQUIDITY_CRUNCH':
        return '📉';
      case 'BEARISH_ACCUMULATION':
        return '💰';
      case 'VOLATILITY_BREAKOUT':
        return '⚡';
      case 'NEUTRAL_TRANSITION':
      default:
        return '⚖️';
    }
  }
}
